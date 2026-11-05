"""Raw terminal input: raw_terminal() and read_key(t).  Spec 19e.

A `Terminal` is a move-only resource: while it is open the terminal delivers each key as it is pressed, with no
echo, no line editing, and no signal keys (Ctrl-C arrives as a key).  Closing it, or the program ending, puts the
terminal back the way it was.
"""
import os
import select
import sys
from .values import *   # noqa
from . import sched as S_
from .prelude import bi, denied

try:
    import termios
except ImportError:          # Windows, the browser
    termios = None

ESC_WAIT = 0.05              # how long a lone Escape waits for the rest of a key sequence


class TermV:
    """The open terminal: a move-only resource that restores the saved settings when it is dropped."""
    __slots__ = ("fd", "saved", "closed", "I")
    tname_ = "Terminal"

    def __init__(self, fd, saved, I):
        self.fd, self.saved, self.closed, self.I = fd, saved, False, I
        I.__dict__.setdefault("live_children", []).append(self)
        I.__dict__["raw_open"] = True

    def drop(self, sched=None):
        if self.closed:
            return
        self.closed = True
        self.I.__dict__["raw_open"] = False
        try:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved)
        except Exception:
            pass


def _raw_settings(attrs):
    a = list(attrs)
    a[0] &= ~(termios.BRKINT | termios.ICRNL | termios.INPCK | termios.ISTRIP | termios.IXON)
    a[3] &= ~(termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)
    cc = list(a[6])
    cc[termios.VMIN], cc[termios.VTIME] = 1, 0
    a[6] = cc
    return a


@bi("raw_terminal")
def b_raw_terminal(I, a, kw, ta):
    import io as _io
    if not I.perms.stdin_ok():
        return denied("raw_terminal", "stdin")
    if (isinstance(I.inp, (_io.StringIO, _io.BytesIO)) or termios is None or not os.isatty(0)
            or getattr(I, "platform", None) == "browser"):
        return err_reserved("MISSING", "standard input is not a terminal")
    if I.__dict__.get("raw_open"):
        raise Abort("a Terminal is already open; close it before opening another")
    try:
        saved = termios.tcgetattr(0)
        termios.tcsetattr(0, termios.TCSADRAIN, _raw_settings(saved))
    except (termios.error, OSError) as e:
        return err_reserved("IO_ERROR", str(e))
    try:
        I.out.flush()
    except Exception:
        pass
    return Ok(TermV(0, saved, I))


# ---------------------------------------------------------------- decoding keys
CSI_TILDE = {1: "Home", 2: "Insert", 3: "Delete", 4: "End", 5: "PageUp", 6: "PageDown", 7: "Home", 8: "End"}
CSI_FKEY = {11: 1, 12: 2, 13: 3, 14: 4, 15: 5, 17: 6, 18: 7, 19: 8, 20: 9, 21: 10, 23: 11, 24: 12}
LETTER = {"A": "Up", "B": "Down", "C": "Right", "D": "Left", "H": "Home", "F": "End"}
SS3_F = {"P": 1, "Q": 2, "R": 3, "S": 4}


def _decode(get, ready):
    """One key from a byte source: `get()` returns the next byte (None at end of input) and `ready()` says whether
    another byte is waiting.  Returns (case-name, payload list) or None at the end of the input."""
    b = get()
    if b is None:
        return None
    if b == 27:
        if not ready():
            return ("Escape", [])
        c = get()
        if c == ord("["):
            return _csi(get)
        if c == ord("O"):
            d = get()
            ch = chr(d) if d is not None else ""
            if ch in LETTER:
                return (LETTER[ch], [])
            if ch in SS3_F:
                return ("Fn", [SS3_F[ch]])
            return ("Other", [])
        if c is None:
            return ("Escape", [])
        if c == 27:
            return ("Escape", [])
        k = _plain(c, get)
        if k[0] == "Typed":
            return ("Alt", k[1])
        return k
    return _plain(b, get)


def _csi(get):
    params, last = "", None
    while True:
        d = get()
        if d is None:
            return ("Other", [])
        ch = chr(d)
        if ch.isdigit() or ch == ";":
            params += ch
            continue
        last = ch
        break
    first = params.split(";")[0]
    n = int(first) if first.isdigit() else 0
    if last in LETTER:
        return (LETTER[last], [])
    if last == "~":
        if n in CSI_TILDE:
            return (CSI_TILDE[n], [])
        if n in CSI_FKEY:
            return ("Fn", [CSI_FKEY[n]])
    return ("Other", [])


def _plain(b, get):
    if b in (10, 13):
        return ("Enter", [])
    if b == 9:
        return ("Tab", [])
    if b in (8, 127):
        return ("Backspace", [])
    if b == 0:
        return ("Ctrl", [Char(" ")])
    if 1 <= b <= 26:
        return ("Ctrl", [Char(chr(b + 96))])
    if b < 32:
        return ("Other", [])
    if b < 128:
        return ("Typed", [Char(chr(b))])
    n = 2 if b >> 5 == 0b110 else 3 if b >> 4 == 0b1110 else 4 if b >> 3 == 0b11110 else 0
    if n == 0:
        return ("Other", [])
    buf = bytes([b])
    for _ in range(n - 1):
        c = get()
        if c is None:
            return ("Other", [])
        buf += bytes([c])
    try:
        return ("Typed", [Char(buf.decode("utf-8"))])
    except UnicodeDecodeError:
        return ("Other", [])


def _fd_source(fd):
    def get():
        try:
            b = os.read(fd, 1)
        except OSError:
            return None
        return b[0] if b else None

    def ready():
        r, _, _ = select.select([fd], [], [], ESC_WAIT)
        return bool(r)
    return get, ready


@bi("read_key", "first", True)
def b_read_key(I, a, kw, ta):
    t = a[0]
    if not isinstance(t, TermV) or t.closed:
        raise Abort("read_key needs an open Terminal")
    get, ready = _fd_source(t.fd)
    k = yield from S_.park_thread(I, lambda: _decode(get, ready))
    if k is None:
        return err_reserved("CLOSED", "end of input")
    name, vals = k
    et = I.enums["Key"].et
    return Ok(I.enum_instance(et, et.cases[name], vals))
