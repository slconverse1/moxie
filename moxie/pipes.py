"""Unix sockets and named pipes: listen_unix, connect_unix, make_fifo, and FIFOs through open_file.  Spec 19c.

A named pipe opened with open_file is an `Io` like a file or a socket, so read_line, lines, read_all, read_bytes,
write, println, write_bytes and close all work on it.  Opening and reading wait on an OS helper thread, so only the
fiber that waits is held up.  Pipes are for talking to other processes; fibers of one program use channels.
"""
import os
import select
import socket
import stat
from .values import *   # noqa
from . import sched as S_
from .prelude import bi, denied, io_error, IoV, ListenerV

POLL = 0.1          # how often a waiting read looks to see whether its end was closed


class PipeR:
    """The read end of a pipe, with its own buffer.  A read that is waiting notices `close` within POLL seconds."""
    def __init__(self, fd):
        self.fd, self.buf, self.closed, self.eof = fd, bytearray(), False, False

    def _fill(self):
        """Wait for more bytes; False at end of input or when this end was closed."""
        while not self.closed:
            try:
                r, _, _ = select.select([self.fd], [], [], POLL)
            except (OSError, ValueError):
                return False
            if r:
                try:
                    d = os.read(self.fd, 65536)
                except OSError:
                    return False
                if not d:
                    self.eof = True
                    return False
                self.buf += d
                return True
        return False

    def readline(self):
        while b"\n" not in self.buf:
            if not self._fill():
                break
        i = self.buf.find(b"\n")
        n = len(self.buf) if i < 0 else i + 1
        out = bytes(self.buf[:n])
        del self.buf[:n]
        return out

    def read(self, n=-1):
        while (n < 0 or len(self.buf) < n) and self._fill():
            pass
        n = len(self.buf) if n < 0 else min(n, len(self.buf))
        out = bytes(self.buf[:n])
        del self.buf[:n]
        return out

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            os.close(self.fd)
        except OSError:
            pass


class PipeW:
    """The write end of a named pipe.  A write waits when the pipe is full, like a write to a socket."""
    def __init__(self, fd):
        self.fd, self.closed = fd, False

    def write(self, data):
        view = memoryview(data)
        while len(view):
            try:
                n = os.write(self.fd, view)
            except BrokenPipeError:
                raise Abort("write to a pipe whose reading end is closed")
            view = view[n:]
        return len(data)

    def flush(self):
        pass

    def close(self):
        if not self.closed:
            self.closed = True
            try:
                os.close(self.fd)
            except OSError:
                pass


def _browser(I):
    return getattr(I, "platform", None) == "browser"


def _unavailable(what):
    return err_reserved("MISSING", f"{what} is not available here")


@bi("make_fifo")
def b_make_fifo(I, a, kw, ta):
    if _browser(I) or not hasattr(os, "mkfifo"):
        return _unavailable("a named pipe")
    if not I.perms.path_ok("fs.write", a[0]):
        return denied(a[0], "fs.write")
    try:
        os.mkfifo(a[0], 0o600)
    except OSError as e:
        return io_error(e, a[0])
    return Ok(UNIT)


def open_fifo(I, path, mode):
    """Generator: open a FIFO for reading or for writing on a helper thread (opening waits for the other end)."""
    if mode == "ReadWrite":
        return err_reserved("IO_ERROR", f"{path}: a named pipe opens for reading or for writing, not both")

    def work():
        try:
            if mode == "ReadOnly":
                return PipeR(os.open(path, os.O_RDONLY))
            return PipeW(os.open(path, os.O_WRONLY))
        except OSError as e:
            return e
    f = yield from S_.park_thread(I, work)
    if isinstance(f, OSError):
        return io_error(f, path)
    return Ok(IoV(I, "file", f))


def is_fifo(path):
    try:
        return stat.S_ISFIFO(os.stat(path).st_mode)
    except OSError:
        return False


# ---------------------------------------------------------------- Unix sockets
class UnixListenerV(ListenerV):
    """A Listener on a path: closing it removes the socket file."""
    __slots__ = ("path",)

    def __init__(self, sock, I, path):
        super().__init__(sock, I)
        self.path = path
        I.__dict__.setdefault("live_children", []).append(self)

    def drop(self, sched=None):
        was = self.closed
        super().drop(sched)
        if not was:
            try:
                os.unlink(self.path)
            except OSError:
                pass


@bi("listen_unix")
def b_listen_unix(I, a, kw, ta):
    path = a[0]
    if _browser(I) or not hasattr(socket, "AF_UNIX"):
        return _unavailable("a Unix socket")
    if not I.perms.path_ok("fs.write", path):
        return denied(path, "fs.write")
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.bind(path)
        s.listen(16)
    except OSError as e:
        s.close()
        return io_error(e, path)
    return Ok(UnixListenerV(s, I, path))


@bi("connect_unix", "first", True)
def b_connect_unix(I, a, kw, ta):
    path = a[0]
    if _browser(I) or not hasattr(socket, "AF_UNIX"):
        return _unavailable("a Unix socket")
    if not I.perms.path_ok("fs.write", path):
        return denied(path, "fs.write")

    def work():
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.connect(path)
            return s
        except OSError as e:
            s.close()
            return e
    s = yield from S_.park_thread(I, work)
    if isinstance(s, OSError):
        return io_error(s, path)
    return Ok(IoV(I, "socket", s.makefile("rwb"), s))
