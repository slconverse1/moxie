"""System basics (Spec 19e): the clock, random numbers, exit codes, signals, and facts about the host.

Everything here reaches outside the program, so the effects pass counts a call as "uses the system"
(a `pure fn`, a contract, and a `forall` body may not make one). Only the calls that can leak or
change something sit behind a permission: `lookup_host` (net.connect) and `make_temp_file` and
`make_temp_dir` (fs.write)."""
import os
import random as _random
import socket
import sys
import tempfile
import time
import signal as _signal
from .values import *   # noqa
from .core import ProgramExit, type_name
from . import sched as S_
from .prelude import bi, denied, io_error, StdStream, IoV, GenR, _fs_guard

_T0 = time.monotonic_ns()


# ---------------------------------------------------------------- clock
# The scheduler's clock is virtual: `sleep` moves it forward without waiting. The clocks here add
# that skew to the real one, so a program that sleeps 100ms always sees at least 100ms pass.
@bi("monotonic")
def b_monotonic(I, a, kw, ta):
    return Dur(time.monotonic_ns() - _T0 + int(I.sched.now))


@bi("now")
def b_now(I, a, kw, ta):
    return Dur(time.time_ns() + int(I.sched.now))


# ---------------------------------------------------------------- random
def _rng(I):
    r = I.__dict__.get("sys_rng")
    if r is None:
        r = I.__dict__["sys_rng"] = _random.Random()
    return r


@bi("random")
def b_random(I, a, kw, ta):
    return _rng(I).random()


@bi("random_int")
def b_random_int(I, a, kw, ta):
    lo, hi = int(a[0]), int(a[1])
    if lo > hi:
        raise Abort(f"random_int: the low end {lo} is above the high end {hi}")
    return _rng(I).randint(lo, hi)


@bi("random_bytes")
def b_random_bytes(I, a, kw, ta):
    n = int(a[0])
    if n < 0:
        raise Abort("random_bytes: the count is negative")
    cls = INT_CLASSES.get("Byte")
    return ArrayV([cls(b) if cls else b for b in os.urandom(n)])


@bi("seeded")
def b_seeded(I, a, kw, ta):
    return GenR(_random.Random(int(a[0])), 8, 0)


# ---------------------------------------------------------------- exit and signals
@bi("exit")
def b_exit(I, a, kw, ta):
    code = int(a[0])
    if not 0 <= code <= 255:
        raise Abort(f"exit: the code {code} is outside 0 to 255")
    raise ProgramExit(code, None)


SIGNALS = (("SIGINT", "interrupt"), ("SIGTERM", "terminate"), ("SIGHUP", "hangup"))


@bi("signals")
def b_signals(I, a, kw, ta):
    ch = S_.Chan(8)
    ch.pools = I.pools
    I.pools.acquire("Chan")
    r, w = S_.ChanR(ch), S_.ChanW(ch)
    sink = S_.EventSink(w, "signals")
    I.__dict__.setdefault("event_sinks", []).append(sink)
    I.sched.listeners += 1
    I.sched.sig_listeners += 1      # an idle program waits for a signal instead of reporting a deadlock
    for sig, name in SIGNALS:
        num = getattr(_signal, sig, None)
        if num is None:
            continue
        try:
            _signal.signal(num, lambda s, f, k=Kw(name): I.sched.post_event(sink, k))
        except ValueError:
            raise Abort("signals must be called from the main thread")
    return r


# ---------------------------------------------------------------- the host
@bi("cwd")
def b_cwd(I, a, kw, ta):
    return os.getcwd()


@bi("home_dir")
def b_home_dir(I, a, kw, ta):
    h = os.path.expanduser("~")
    if h == "~" or not os.path.isdir(h):
        return err_reserved("MISSING", "no home directory")
    return Ok(h)


@bi("temp_dir")
def b_temp_dir(I, a, kw, ta):
    return tempfile.gettempdir()


@bi("hostname")
def b_hostname(I, a, kw, ta):
    return socket.gethostname()


@bi("os_name")
def b_os_name(I, a, kw, ta):
    p = sys.platform
    if getattr(I, "platform", None) == "browser" or p == "emscripten":
        return "browser"
    return "linux" if p.startswith("linux") else "macos" if p == "darwin" else "windows" if p == "win32" else p


@bi("is_terminal")
def b_is_terminal(I, a, kw, ta):
    x = a[0]
    if isinstance(x, StdStream):
        try:
            return os.isatty({"stdin": 0, "stdout": 1, "stderr": 2}[x.kind])
        except OSError:
            return False
    if isinstance(x, IoV):
        return False
    raise Abort(f"is_terminal needs stdin, stdout, stderr, or an Io, not {type_name(x)}")


@bi("terminal_size")
def b_terminal_size(I, a, kw, ta):
    for fd in (1, 2, 0):
        try:
            sz = os.get_terminal_size(fd)
            return Ok(TupleV([sz.columns, sz.lines], ["cols", "rows"]))
        except OSError:
            continue
    return err_reserved("MISSING", "not a terminal")


@bi("lookup_host", "first", True)
def b_lookup_host(I, a, kw, ta):
    host = a[0]
    if not I.perms.connect_ok(host, "*"):
        return denied(host, "net.connect")

    def work():
        try:
            seen = []
            for fam, _t, _p, _c, sa in socket.getaddrinfo(host, None):
                if sa[0] not in seen:
                    seen.append(sa[0])
            return seen
        except OSError as e:
            return e
    r = yield from S_.park_thread(I, work)
    if isinstance(r, OSError):
        return err_reserved("NOT_FOUND", f"{host}: name not found")
    return Ok(ListV(r, max(len(r), 1)))


def _temp(I, kind, prefix):
    d = _fs_guard(I, "fs.write", tempfile.gettempdir())
    if d is not None:
        return d
    try:
        if kind == "file":
            fd, p = tempfile.mkstemp(prefix=prefix)
            os.close(fd)
        else:
            p = tempfile.mkdtemp(prefix=prefix)
    except OSError as e:
        return io_error(e, tempfile.gettempdir())
    return Ok(p)


@bi("make_temp_file")
def b_make_temp_file(I, a, kw, ta):
    return _temp(I, "file", a[0] if a else "moxie-")


@bi("make_temp_dir")
def b_make_temp_dir(I, a, kw, ta):
    return _temp(I, "dir", a[0] if a else "moxie-")


# ---------------------------------------------------------------- durations out to numbers
def _dur(a, who):
    if not isinstance(a[0], Dur):
        raise Abort(f"{who} needs a Duration, not {type_name(a[0])}")
    return a[0].ns


@bi("nanos")
def b_nanos(I, a, kw, ta):
    return _dur(a, "nanos")


@bi("millis")
def b_millis(I, a, kw, ta):
    return _dur(a, "millis") // 1_000_000


@bi("seconds")
def b_seconds(I, a, kw, ta):
    return _dur(a, "seconds") / 1e9
