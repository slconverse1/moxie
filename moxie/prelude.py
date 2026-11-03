"""The Moxie prelude: built-in functions and types."""
import math
from functools import cmp_to_key
from .ast import *   # noqa
from .values import *   # noqa
from .core import *   # noqa
from .types_ import *   # noqa
from .calls import END, USING, SLOT, LazyV, GenV
from .streams import *   # noqa
from .streams import make_iter, drain, stream_of, is_streamable
from . import sched as S_


REG = {}


def bi(name, pos="first", gen=False):
    def deco(fn):
        REG[name] = (fn, pos, gen)
        return fn
    return deco


def install_prelude(I):
    env = I.prelude
    env.vars["stdin"], env.vars["stdout"], env.vars["stderr"] = STDIN, STDOUT, STDERR
    for name, (fn, pos, gen) in REG.items():
        b = Builtin(fn, name, gen)
        b.pre = pos
        env.vars[name] = b
    for _k, _c in ERR_CODES.items():
        env.vars[_k] = _c          # the reserved Error codes: CLOSED, MISSING, ...
    env.vars["NAN"] = math.nan
    env.vars["INF"] = math.inf
    env.vars["MAX"] = INT_MAX
    env.vars["MIN"] = INT_MIN
    env.vars["args"] = ArrayV([])
    env.vars["env"] = DictV({}, 0)
    ml = TupleV([",", "."], ["group", "decimal"], "Locale")
    env.vars["Locale"] = TypeV("Locale", None)
    env.vars["Connection"] = TypeV("Connection", None)
    I.tuples["Locale"] = TypeInfo("Locale", [], [FieldDecl("group", TName(["String"], []), None, None), FieldDecl("decimal", TName(["String"], []), None, None)], [])
    I.tuples["Locale"].env = env
    I.locales = {"de_de": TupleV([".", ","], ["group", "decimal"], "Locale"),
                 "en_us": TupleV([",", "."], ["group", "decimal"], "Locale"),
                 "fr_fr": TupleV([" ", ","], ["group", "decimal"], "Locale")}
    I.exports = {}
    I._last_self = None
    I.depth = 0
    I.locale_type = env.vars["Locale"]
    I.prelude.vars["Result"] = TypeV("Result", None)
    I.sched = S_.Scheduler(I)


def make_iter_(self, v):
    return make_iter(self, v)


def iter_next_(self, it):
    return it.nxt()


from .interp import Interp as _I  # noqa  (circular-safe: attached after class creation)


# ---------------------------------------------------------------- output
class StdStream:
    """standard input, output or error: a value the runtime owns (borrowed, never moved or closed)."""
    __slots__ = ("kind",)
    tname_ = "Stdio"

    def __init__(self, kind):
        self.kind = kind

    def drop(self, sched=None):
        raise Abort(f"{self.kind} belongs to the runtime and cannot be closed")

    def __repr__(self):
        return self.kind


STDIN, STDOUT, STDERR = StdStream("stdin"), StdStream("stdout"), StdStream("stderr")


class IoV:
    """A file or a socket: a move-only resource wrapping a binary Python file object (Spec 19c)."""
    __slots__ = ("kind", "f", "sock", "closed", "I")
    tname_ = "Io"

    def __init__(self, I, kind, f, sock=None):
        self.kind, self.f, self.sock, self.closed, self.I = kind, f, sock, False, I
        I.__dict__.setdefault("live_io", []).append(self)

    def drop(self, sched=None):
        if self.closed:
            return
        self.closed = True
        for x in (self.f, self.sock):
            try:
                if x is not None:
                    x.close()
            except Exception:
                pass

    def write(self, s):
        self.f.write(s.encode("utf-8"))
        if self.kind == "socket":          # a socket sends each write at once
            self.f.flush()

    def flush(self):
        self.f.flush()

    def __repr__(self):
        return f"<{self.kind} {'closed' if self.closed else 'open'}>"


class ListenerV:
    __slots__ = ("sock", "closed")
    tname_ = "Listener"

    def __init__(self, sock):
        self.sock, self.closed = sock, False

    def drop(self, sched=None):
        if not self.closed:
            self.closed = True
            try:
                self.sock.close()
            except Exception:
                pass


def io_error(e, what=""):
    import errno
    code = "IO_ERROR"
    if isinstance(e, FileNotFoundError) or getattr(e, "errno", None) == errno.ENOENT:
        code = "NOT_FOUND"
    elif isinstance(e, PermissionError):
        code = "DENIED"
    return err_reserved(code, (what + ": " if what else "") + (e.strerror or str(e)))


def close_live_io(I):
    for x in list(I.__dict__.get("live_io", [])):
        x.drop()


def _sink(I, h):
    if h is STDOUT:
        return I.out
    if h is STDERR:
        return I.err
    if isinstance(h, IoV):
        if h.closed:
            raise Abort("write to a closed file or socket")
        return h
    raise Abort(f"cannot write to {h.kind if isinstance(h, StdStream) else type_name(h)}")


def _emit(I, a, nl):
    if len(a) >= 2 and isinstance(a[0], (StdStream, IoV)):
        s = display(a[1], I)
        sink = _sink(I, a[0])
    else:
        s = display(a[0], I) if a else ""
        sink = I.out
    sink.write(s + ("\n" if nl else ""))
    return UNIT


@bi("println")
def b_println(I, a, kw, ta):
    return _emit(I, a, True)


@bi("print")
def b_print(I, a, kw, ta):
    return _emit(I, a, False)


@bi("eprintln")
def b_eprintln(I, a, kw, ta):
    return _emit(I, [STDERR, a[0] if a else ""], True)


@bi("eprint")
def b_eprint(I, a, kw, ta):
    return _emit(I, [STDERR, a[0] if a else ""], False)


@bi("flush")
def b_flush(I, a, kw, ta):
    for s in ([_sink(I, a[0])] if a else [I.out, I.err]):
        try:
            s.flush()
        except Exception:
            pass
    return UNIT


def _inp(I, a):
    if a and isinstance(a[0], IoV):
        if a[0].closed:
            raise Abort("read from a closed file or socket")
        return a[0].f
    if a and a[0] is not STDIN:
        raise Abort("a read needs stdin or an open file or socket")
    return I.inp


def _prompt_flush(I):
    try:
        if I.out.isatty():
            I.out.flush()
    except Exception:
        pass


def _read_line_f(f):
    try:
        raw = f.buffer.readline() if hasattr(f, "buffer") else f.readline()
    except OSError as e:
        return io_error(e)
    except Exception as e:
        return err_reserved("CLOSED", str(e))
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if not raw:
        return err_reserved("CLOSED", "end of input")
    try:
        line = raw.decode("utf-8")
    except UnicodeDecodeError:
        return err_reserved("BAD_ENCODING", "input is not valid UTF-8")
    if line.endswith("\n"):
        line = line[:-1]
        if line.endswith("\r"):
            line = line[:-1]
    return Ok(line)


def _blocking(I, f, fn):
    """Run a blocking read: inline when the source is in memory, else on a helper OS thread."""
    import io as _io
    if isinstance(f, (_io.BytesIO, _io.StringIO)):
        return Done(fn())
    return S_.park_thread(I, fn)


def _read_line(I, a):
    f = _inp(I, a)
    _prompt_flush(I)
    return (yield from _blocking(I, f, lambda: _read_line_f(f)))


@bi("read_line", "first", True)
def b_read_line(I, a, kw, ta):
    return (yield from _read_line(I, a))


@bi("read_all", "first", True)
def b_read_all(I, a, kw, ta):
    f = _inp(I, a)
    _prompt_flush(I)

    def work():
        try:
            raw = f.buffer.read() if hasattr(f, "buffer") else f.read()
        except OSError as e:
            return io_error(e)
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        try:
            return Ok(raw.decode("utf-8"))
        except UnicodeDecodeError:
            return err_reserved("BAD_ENCODING", "input is not valid UTF-8")
    return (yield from _blocking(I, f, work))


class StdinLinesIter:
    __slots__ = ("I", "a")

    def __init__(self, I, a=()):
        self.I, self.a = I, list(a)

    def nxt(self):
        r = yield from _read_line(self.I, self.a)
        if r.case == "Ok":
            return r.vals[0]
        if r.vals[0].vals[0] == ERR_CODES["CLOSED"]:
            return END
        raise Abort("lines: " + r.vals[0].vals[1])


@bi("stdin_lines")
def b_stdin_lines(I, a, kw, ta):
    return StreamV(lambda: StdinLinesIter(I))


@bi("lines")
def b_lines(I, a, kw, ta):
    if not a or not isinstance(a[0], (IoV, StdStream)):
        raise Abort("lines needs stdin, a file, or a socket")
    return StreamV(lambda: StdinLinesIter(I, [a[0]]))


def _mode_of(m):
    return m.case if isinstance(m, EnumV) else str(m)


@bi("open_file")
def b_open_file(I, a, kw, ta):
    path, mode = a[0], _mode_of(a[1]) if len(a) > 1 else "ReadOnly"
    pm = {"ReadOnly": "rb", "Create": "wb", "Append": "ab", "ReadWrite": "r+b"}.get(mode)
    if pm is None:
        raise Abort(f"open_file: unknown mode {mode}")
    try:
        return Ok(IoV(I, "file", open(path, pm)))
    except OSError as e:
        return io_error(e, path)


@bi("read_file")
def b_read_file(I, a, kw, ta):
    try:
        raw = open(a[0], "rb").read()
    except OSError as e:
        return io_error(e, a[0])
    try:
        return Ok(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return err_reserved("BAD_ENCODING", a[0] + " is not valid UTF-8")


@bi("write_file")
def b_write_file(I, a, kw, ta):
    try:
        with open(a[0], "wb") as f:
            f.write(a[1].encode("utf-8"))
    except OSError as e:
        return io_error(e, a[0])
    return Ok(UNIT)


@bi("read_bytes", "first", True)
def b_read_bytes(I, a, kw, ta):
    f = _inp(I, a)

    def work():
        try:
            return (f.buffer if hasattr(f, "buffer") else f).read(int(a[1]))
        except OSError as e:
            return e
    raw = yield from _blocking(I, f, work)
    if isinstance(raw, OSError):
        return io_error(raw)
    cls = INT_CLASSES.get("UInt8")
    return Ok(ArrayV([cls(b) if cls else b for b in raw]))


@bi("write_bytes")
def b_write_bytes(I, a, kw, ta):
    h = a[0]
    if not isinstance(h, IoV) or h.closed:
        raise Abort("write_bytes needs an open file or socket")
    try:
        h.f.write(bytes(int(x) for x in a[1].items))
        if h.kind == "socket":
            h.f.flush()
    except OSError as e:
        return io_error(e)
    return Ok(UNIT)


@bi("connect", "first", True)
def b_connect(I, a, kw, ta):
    import socket

    def work():
        try:
            s = socket.create_connection((a[0], int(a[1])), timeout=30)
            s.settimeout(None)
            return s
        except OSError as e:
            return e
    s = yield from S_.park_thread(I, work)
    if isinstance(s, OSError):
        return io_error(s, f"{a[0]}:{a[1]}")
    return Ok(IoV(I, "socket", s.makefile("rwb"), s))


@bi("listen")
def b_listen(I, a, kw, ta):
    import socket
    try:
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", int(a[0])))
        s.listen(16)
        return Ok(ListenerV(s))
    except OSError as e:
        return io_error(e, f"port {a[0]}")


@bi("port_of")
def b_port_of(I, a, kw, ta):
    return a[0].sock.getsockname()[1]


@bi("accept", "first", True)
def b_accept(I, a, kw, ta):
    l = a[0]
    if not isinstance(l, ListenerV) or l.closed:
        raise Abort("accept needs an open Listener")

    def work():
        try:
            return l.sock.accept()[0]
        except OSError as e:
            return e
    c = yield from S_.park_thread(I, work)
    if isinstance(c, OSError):
        return io_error(c)
    return Ok(IoV(I, "socket", c.makefile("rwb"), c))


@bi("with_stdin", "first", True)
def b_with_stdin(I, a, kw, ta):
    """with_stdin(text, f): run f() with `text` as standard input (for tests and doctests)."""
    import io as _io
    saved = I.inp
    I.inp = _io.BytesIO(a[0].encode("utf-8") if isinstance(a[0], str) else bytes(a[0]))
    try:
        return (yield from I.apply(a[1], [], {}))
    finally:
        I.inp = saved


@bi("dbg")
def b_dbg(I, a, kw, ta):
    I.err.write(f"[dbg {I.file}:{I.line}] {show(a[0], I)}\n")
    return a[0]


@bi("cstr")
def b_cstr(I, a, kw, ta):
    """cstr(text): a NUL-terminated copy of a String, for a foreign function."""
    from .ffi import CStringV
    return CStringV(a[0].encode("utf-8") + b"\0")


@bi("trace")
def b_trace(I, a, kw, ta):
    """A debug message to the error stream; exempt from effect inference; off under --release."""
    if CONTRACTS[0]:
        t = a[0] if isinstance(a[0], str) else show(a[0], I)
        I.err.write(f"[trace {I.file}:{I.line}] {t}\n")
    return UNIT


@bi("show")
def b_show(I, a, kw, ta):
    return show(a[0], I)


@bi("hash")
def b_hash(I, a, kw, ta):
    """Hashable: a deterministic hash of the value's content (equal values hash alike)."""
    x = a[0]

    def walk(v):
        if isinstance(v, float):
            raise Abort("a Float or Double is not Hashable (NaN breaks equality)")
        if isinstance(v, (Seq, TupleV)):
            for e in (v.items if isinstance(v, Seq) else v.vals):
                walk(e)
        return None
    walk(x)
    h = 1469598103934665603
    for b in (type_name(x) + ":" + show(x, I)).encode("utf-8"):
        h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h & 0x7FFFFFFFFFFFFFFF


# ---------------------------------------------------------------- sizes and text
@bi("len")
def b_len(I, a, kw, ta):
    c = a[0]
    if isinstance(c, str):
        return len(c.encode("utf-8"))
    if isinstance(c, (Seq, SetV, DictV, MultiV)):
        return len(c)
    if isinstance(c, TupleV):
        return len(c.vals)
    raise Abort(f"len of {type_name(c)}")


@bi("char_count")
def b_char_count(I, a, kw, ta):
    return len(a[0])


@bi("chars")
def b_chars(I, a, kw, ta):
    return StreamV(lambda s=a[0]: ListIter([Char(c) for c in s]))


@bi("pad_left")
def b_pad_left(I, a, kw, ta):
    return pad_text(a[0], a[1], a[2] if len(a) > 2 else " ", ">")


@bi("pad_right")
def b_pad_right(I, a, kw, ta):
    return pad_text(a[0], a[1], a[2] if len(a) > 2 else " ", "<")


@bi("split")
def b_split(I, a, kw, ta):
    s, sep = a[0], a[1]
    parts = s.split(sep) if sep != "" else list(s)
    return ListV(parts, max(len(parts), 1))


@bi("join")
def b_join(I, a, kw, ta):
    xs, sep = a[0], (a[1] if len(a) > 1 else "")
    items = xs.items if isinstance(xs, Seq) else list(xs)
    return sep.join(display(x, I) for x in items)


@bi("trim")
def b_trim(I, a, kw, ta):
    return a[0].strip()


@bi("starts_with")
def b_starts_with(I, a, kw, ta):
    return a[0].startswith(a[1])


@bi("ends_with")
def b_ends_with(I, a, kw, ta):
    return a[0].endswith(a[1])


@bi("contains")
def b_contains(I, a, kw, ta):
    return I.contains(a[0], a[1])


@bi("upper")
def b_upper(I, a, kw, ta):
    return a[0].upper()


@bi("lower")
def b_lower(I, a, kw, ta):
    return a[0].lower()


@bi("replace_text")
def b_replace_text(I, a, kw, ta):
    return a[0].replace(a[1], a[2])


# ---------------------------------------------------------------- numbers
@bi("abs")
def b_abs(I, a, kw, ta):
    x = a[0]
    if isinstance(x, FixedInt):
        return int_result(x.__class__, abs(int(x)))
    if x.__class__ is int and x == INT_MIN:
        raise Abort("Int overflow")
    return abs(x) if not isinstance(x, Dec) else Dec(abs(x.v), x.scale)


@bi("min")
def b_min(I, a, kw, ta):
    if len(a) == 1:
        return (yield from _ext(I, a[0], "min"))
    return a[0] if not lt(a[1], a[0]) else a[1]


b_min = REG["min"] = (b_min, "first", True)


@bi("max")
def b_max(I, a, kw, ta):
    if len(a) == 1:
        return (yield from _ext(I, a[0], "max"))
    return a[0] if not lt(a[0], a[1]) else a[1]


REG["max"] = (REG["max"][0], "first", True)


def _ext(I, src, which):
    items = yield from drain(I, src)
    if not items:
        return err_reserved("MISSING", "empty")
    best = items[0]
    for x in items[1:]:
        if which == "min" and lt(x, best):
            best = x
        elif which == "max" and lt(best, x):
            best = x
    return Ok(best)


@bi("clamp")
def b_clamp(I, a, kw, ta):
    x, lo, hi = a
    if lt(x, lo):
        return lo
    if lt(hi, x):
        return hi
    return x


@bi("pow")
def b_pow(I, a, kw, ta):
    x, y = a
    if isinstance(x, float) or isinstance(y, float):
        return math.pow(x, y)
    return arith_pow(x, y)


def arith_pow(x, y):
    r = int(x) ** int(y)
    if isinstance(x, FixedInt):
        return int_result(x.__class__, r)
    return int_result(int, r)


@bi("sqrt")
def b_sqrt(I, a, kw, ta):
    x = float(a[0])
    return math.sqrt(x) if x >= 0 else math.nan


@bi("floor")
def b_floor(I, a, kw, ta):
    return math.floor(a[0])


@bi("ceil")
def b_ceil(I, a, kw, ta):
    return math.ceil(a[0])


@bi("round")
def b_round(I, a, kw, ta):
    return int(math.floor(a[0] + 0.5))


@bi("is_nan")
def b_is_nan(I, a, kw, ta):
    return a[0] != a[0]


@bi("is_inf")
def b_is_inf(I, a, kw, ta):
    return a[0] in (math.inf, -math.inf)


@bi("is_finite")
def b_is_finite(I, a, kw, ta):
    return math.isfinite(a[0])


@bi("finite")
def b_finite(I, a, kw, ta):
    return Ok(a[0]) if math.isfinite(a[0]) else err_reserved("OUT_OF_RANGE", "not finite")


def int_class_of(x, b=None):
    if isinstance(x, FixedInt):
        return x.__class__
    if isinstance(b, FixedInt):
        return b.__class__
    return int


def _wide(x, b):
    c = int_class_of(x, b)
    return c


@bi("wrapping_add")
def b_wadd(I, a, kw, ta):
    c = _wide(*a)
    r = int(a[0]) + int(a[1])
    return _wrap(c, r)


@bi("wrapping_sub")
def b_wsub(I, a, kw, ta):
    return _wrap(_wide(*a), int(a[0]) - int(a[1]))


@bi("wrapping_mul")
def b_wmul(I, a, kw, ta):
    return _wrap(_wide(*a), int(a[0]) * int(a[1]))


def _wrap(c, r):
    if c is int:
        return ((r + (1 << 63)) % (1 << 64)) - (1 << 63)
    return c.wrap(r)


def _sat(c, r):
    if c is int:
        return max(INT_MIN, min(INT_MAX, r))
    return c(max(c.lo(), min(c.hi(), r)))


@bi("saturating_add")
def b_sadd(I, a, kw, ta):
    return _sat(_wide(*a), int(a[0]) + int(a[1]))


@bi("saturating_sub")
def b_ssub(I, a, kw, ta):
    return _sat(_wide(*a), int(a[0]) - int(a[1]))


@bi("saturating_mul")
def b_smul(I, a, kw, ta):
    return _sat(_wide(*a), int(a[0]) * int(a[1]))


def _checked(c, r):
    lo, hi = (INT_MIN, INT_MAX) if c is int else (c.lo(), c.hi())
    if lo <= r <= hi:
        return Ok(r if c is int else c(r))
    return err_reserved("OUT_OF_RANGE", "overflow")


@bi("checked_add")
def b_cadd(I, a, kw, ta):
    if isinstance(a[0], float):
        return b_finite(I, [a[0] + a[1]], kw, ta)
    return _checked(_wide(*a), int(a[0]) + int(a[1]))


@bi("checked_sub")
def b_csub(I, a, kw, ta):
    if isinstance(a[0], float):
        return b_finite(I, [a[0] - a[1]], kw, ta)
    return _checked(_wide(*a), int(a[0]) - int(a[1]))


@bi("checked_mul")
def b_cmul(I, a, kw, ta):
    if isinstance(a[0], float):
        return b_finite(I, [a[0] * a[1]], kw, ta)
    return _checked(_wide(*a), int(a[0]) * int(a[1]))


@bi("checked_div")
def b_cdiv(I, a, kw, ta):
    if a[1] == 0:
        return err_reserved("OUT_OF_RANGE", "division by zero")
    if isinstance(a[0], float):
        return b_finite(I, [a[0] / a[1]], kw, ta)
    return _checked(_wide(*a), idiv(int(a[0]), int(a[1])))


def targ_type(I, ta):
    if not ta or not ta[0]:
        raise Abort("this function needs a type argument, such as cast[Int8](x)")
    return ta[0][0]


@bi("cast")
def b_cast(I, a, kw, ta):
    t = targ_type(I, ta)
    return I.cast_to(a[0], t, "abort")


@bi("try_cast")
def b_try_cast(I, a, kw, ta):
    t = targ_type(I, ta)
    return I.cast_to(a[0], t, "result")


@bi("wrap_to")
def b_wrap_to(I, a, kw, ta):
    t = targ_type(I, ta)
    return I.cast_to(a[0], t, "wrap")


def cast_to(self, v, t, mode):
    name = t.path[-1] if isinstance(t, TName) else None
    base = name
    tn = t
    # aliases / bounded types
    if name in self.aliases:
        kind, inner, tp = self.aliases[name]
        rng = self.bounded_range(inner, self.module_env) if isinstance(inner, TName) else None
        if rng is not None and isinstance(v, int):
            lo, hi = rng
            if (lo is not None and v < lo) or (hi is not None and v > hi):
                if mode == "result":
                    return err_reserved("OUT_OF_RANGE", "out of range")
                raise Abort(f"{v} is out of range for {name}")
            return Ok(v) if mode == "result" else v
        return self.cast_to(v, inner, mode)
    if name == "Char":
        r = Char(chr(int(v)))
        return Ok(r) if mode == "result" else r
    cls = INT_CLASSES.get(name)
    if name == "Int":
        cls = int
    if name == "BigInt":
        bits = self.run_sync(self.ev(t.groups[0][0].expr, self.module_env))
        cls = bigint_class(bits)
    if cls is not None:
        if isinstance(v, Char):
            iv = ord(v)
        elif isinstance(v, float):
            if v != v or v in (math.inf, -math.inf):
                if mode == "result":
                    return err_reserved("OUT_OF_RANGE", "not finite")
                raise Abort("cannot cast a non-finite float")
            iv = int(v)
        else:
            iv = int(v)
        if cls is int:
            lo, hi = INT_MIN, INT_MAX
        else:
            lo, hi = cls.lo(), cls.hi()
        if lo <= iv <= hi:
            r = iv if cls is int else cls(iv)
            return Ok(r) if mode == "result" else r
        if mode == "wrap":
            return _wrap(cls, iv)
        if mode == "result":
            return err_reserved("OUT_OF_RANGE", "does not fit")
        raise Abort(f"{iv} does not fit {name}")
    if name in ("Double", "LongDouble"):
        r = float(v)
        return Ok(r) if mode == "result" else r
    if name == "Float":
        r = F32.of(float(v))
        return Ok(r) if mode == "result" else r
    return Ok(v) if mode == "result" else v


import types as _types
_I.cast_to = cast_to
_I.make_iter = make_iter_
_I.iter_next = iter_next_


@bi("round_to")
def b_round_to(I, a, kw, ta):
    scale = I.run_sync(I.ev(ta[0][0].expr, I.module_env)) if ta else 0
    x, mode = a[0], a[1]
    mode = ROUNDING[str(mode)]
    q = Decimal(1).scaleb(-scale)
    v = x.v if isinstance(x, Dec) else Decimal(str(x))
    return Dec(v.quantize(q, rounding=mode), scale)


@bi("div")
def b_div(I, a, kw, ta):
    x, y, scale, mode = a
    q = Decimal(1).scaleb(-scale)
    return Dec((to_dec(x).v / to_dec(y).v).quantize(q, rounding=ROUNDING[str(mode)]), scale)


@bi("parse_number")
def b_parse_number(I, a, kw, ta):
    s = a[0]
    loc = None
    if len(a) > 1 and isinstance(a[1], TupleV):
        loc = dict(zip(a[1].names, a[1].vals))
    if loc:
        s = s.replace(loc["group"], "").replace(loc["decimal"], ".")
    try:
        if "." in s:
            return Ok(float(s))
        return Ok(int(s))
    except ValueError:
        return err_reserved("MISSING", "not a number")


@bi("read")
def b_read(I, a, kw, ta):
    x = a[0]
    if hasattr(x, "chan_read"):
        return (yield from x.chan_read(I))
    if isinstance(x, str):
        return I.read_text(x, ta)
    if isinstance(x, S_.FutureR):
        return x.snapshot()
    raise Abort(f"cannot read from {type_name(x)}")


REG["read"] = (REG["read"][0], "first", True)


def read_text(self, s, ta):
    """read[T](text) for deriving read."""
    t = ta[0][0] if ta and ta[0] else None
    name = t.path[-1] if isinstance(t, TName) else None
    s = s.strip()
    if name in self.tuples:
        info = self.tuples[name]
        import re
        m = re.match(r"^" + re.escape(name) + r"\((.*)\)$", s, re.S)
        if not m:
            return err_reserved("MISSING", "cannot read")
        body = m.group(1)
        vals = []
        for part in split_top(body):
            if ":" in part:
                part = part.split(":", 1)[1].strip()
            vals.append(self.parse_scalar(part))
        return Ok(TupleV(vals, info.names, name))
    try:
        return Ok(self.parse_scalar(s))
    except Exception:
        return err_reserved("MISSING", "cannot read")


def split_top(s):
    out, depth, cur, q = [], 0, "", False
    for c in s:
        if c == '"':
            q = not q
        if not q:
            if c in "([":
                depth += 1
            elif c in ")]":
                depth -= 1
            elif c == "," and depth == 0:
                out.append(cur.strip())
                cur = ""
                continue
        cur += c
    if cur.strip():
        out.append(cur.strip())
    return out


def parse_scalar(self, s):
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    if s in ("true", "false"):
        return s == "true"
    if "." in s or "e" in s.lower():
        return float(s)
    return int(s)


_I.read_text = read_text
_I.parse_scalar = parse_scalar


# ---------------------------------------------------------------- Result helpers
@bi("is_ok")
def b_is_ok(I, a, kw, ta):
    return is_ok(a[0])


@bi("is_err")
def b_is_err(I, a, kw, ta):
    return is_err(a[0])


@bi("map_ok", "first", True)
def b_map_ok(I, a, kw, ta):
    r, f = a[0], a[1]
    if is_ok(r):
        return Ok((yield from I.apply(f, [r.vals[0]])))
    return r


@bi("map_err", "first", True)
def b_map_err(I, a, kw, ta):
    r, f = a[0], a[1]
    if is_err(r):
        return Err((yield from I.apply(f, [r.vals[0]])))
    return r


@bi("or_else", "first", True)
def b_or_else(I, a, kw, ta):
    r, f = a[0], a[1]
    if is_err(r):
        return (yield from I.apply(f, [r.vals[0]]))
    return r


@bi("ensure")
def b_ensure(I, a, kw, ta):
    return Ok(UNIT) if a[0] else Err(a[1])


@bi("guard")
def b_guard(I, a, kw, ta):
    mt = I.enums.get("Maybe")
    if a[0]:
        return Ok(UNIT) if mt is None else I.enum_instance(mt.et, mt.et.cases["Just"], [UNIT]) if False else Ok(UNIT)
    return err_reserved("MISSING", "guard")


@bi("fail")
def b_fail(I, a, kw, ta):
    code = a[0]
    if isinstance(code, int) and code in ERR_NAMES and False:
        raise Abort("reserved error code")
    return Err(make_error(code, a[1] if len(a) > 1 else ""))


@bi("Error")
def b_Error(I, a, kw, ta):
    pos = list(a)
    code = kw["code"] if "code" in kw else (pos.pop(0) if pos else 0)
    msg = kw["message"] if "message" in kw else (pos.pop(0) if pos else "")
    return make_error(code, msg)


@bi("Ok")
def b_Ok(I, a, kw, ta):
    return Ok(a[0])


@bi("Err")
def b_Err(I, a, kw, ta):
    return Err(a[0])


@bi("get_or")
def b_get_or(I, a, kw, ta):
    x = a[0]
    if isinstance(x, EnumV) and x.et is RESULT_T:
        return x.vals[0] if x.case == "Ok" else a[1]
    if isinstance(x, EnumV) and x.case == "Just":
        return x.vals[0]
    if isinstance(x, EnumV) and x.case == "Nothing":
        return a[1]
    r = I.index_get_safe(x, a[1])
    return r if r is not MISSING else a[2]


def index_get_safe(self, coll, key):
    if isinstance(coll, DictV):
        return coll.d.get(key, MISSING)
    if isinstance(coll, Seq):
        return coll.items[key] if isinstance(key, int) and 0 <= key < len(coll.items) else MISSING
    if isinstance(coll, str):
        return MISSING
    return MISSING


_I.index_get_safe = index_get_safe


@bi("get")
def b_get(I, a, kw, ta):
    x, k = a[0], a[1]
    r = I.index_get_safe(x, k)
    if isinstance(x, TupleV):
        return I.index_get(x, [k])
    if r is MISSING:
        return err_reserved("MISSING" if isinstance(x, DictV) else "OUT_OF_RANGE", "no such element")
    return Ok(r)


@bi("unwrap")
def b_unwrap(I, a, kw, ta):
    if is_ok(a[0]):
        return a[0].vals[0]
    raise Abort("unwrap of an Err")


# ---------------------------------------------------------------- collections
@bi("set")
def b_set(I, a, kw, ta):
    return I.set_index(a[0], [a[1]], a[2])


@bi("put")
def b_put(I, a, kw, ta):
    c = a[0]
    if GC[0]:
        # moxie/gc: put returns the updated collection and cannot fail for lack of room
        if isinstance(c, DictV):
            d = dict(c.d)
            d[a[1]] = a[2]
            return DictV(d)
        if isinstance(c, ListV):
            return ListV(c.items + [a[1]])
        if isinstance(c, SetV):
            d = dict(c.items)
            d[a[1]] = True
            return SetV(d)
        raise Abort("put on " + type_name(c))
    if isinstance(c, DictV):
        if a[1] not in c.d and len(c.d) >= c.cap:
            return err_reserved("NO_SLOT", "Dict is full")
        d = dict(c.d)
        d[a[1]] = a[2]
        return Ok(DictV(d, c.cap))
    if isinstance(c, ListV):
        if len(c.items) >= c.cap:
            return err_reserved("NO_SLOT", "List is full")
        return Ok(ListV(c.items + [a[1]], c.cap))
    if isinstance(c, SetV):
        if a[1] not in c.items and len(c.items) >= c.cap:
            return err_reserved("NO_SLOT", "Set is full")
        d = dict(c.items)
        d[a[1]] = True
        return Ok(SetV(d, c.cap))
    raise Abort("put on " + type_name(c))


@bi("copy")
def b_copy(I, a, kw, ta):
    if GC[0]:
        raise Abort("`copy` does not exist in moxie/gc: a slice is already an ordinary value")
    return a[0]


@bi("clear")
def b_clear(I, a, kw, ta):
    c = a[0]
    if isinstance(c, ListV):
        return ListV([], c.cap)
    if isinstance(c, DictV):
        return DictV({}, c.cap)
    if isinstance(c, SetV):
        return SetV({}, c.cap)
    return c


@bi("keys")
def b_keys(I, a, kw, ta):
    d = a[0]
    return StreamV(lambda: ListIter(list(d.d.keys())))


@bi("values")
def b_values(I, a, kw, ta):
    d = a[0]
    if isinstance(d, TypeV):
        return I.type_member(d, "values", 0).fn(I, [], {}, None)
    return StreamV(lambda: ListIter(list(d.d.values())))


@bi("items")
def b_items(I, a, kw, ta):
    d = a[0]
    return StreamV(lambda: make_iter(I, d))


@bi("remove")
def b_remove(I, a, kw, ta):
    c, k = a[0], a[1]
    if isinstance(c, DictV):
        d = dict(c.d)
        d.pop(k, None)
        return DictV(d, c.cap)
    if isinstance(c, SetV):
        d = dict(c.items)
        d.pop(k, None)
        return SetV(d, c.cap)
    if isinstance(c, Seq):
        items = list(c.items)
        for i, x in enumerate(items):
            if x == k:
                del items[i]
                break
        return type(c)(items, c.cap)
    raise Abort("remove on " + type_name(c))


@bi("remove_at")
def b_remove_at(I, a, kw, ta):
    c, i = a
    if not 0 <= i < len(c.items):
        raise Abort(f"index {i} out of range")
    items = list(c.items)
    del items[i]
    return type(c)(items, c.cap)


@bi("fill")
def b_fill(I, a, kw, ta):
    return ("fill", a[0])


@bi("index")
def b_index(I, a, kw, ta):
    v = a[0]
    if isinstance(v, EnumV):
        return v.et.cases[v.case].index
    raise Abort("index of " + type_name(v))


def _coll_ctor(kind):
    def ctor(I, a, kw, ta):
        groups = ta or []
        cap = None
        if len(groups) > 1 and groups[1]:
            cap = I.const_of(groups[1][0], I.module_env)
        if kind == "Dict":
            d = {}
            for k, v in kw.items():
                d[k] = v
            for x in a:
                if isinstance(x, TupleV):
                    d[x.vals[0]] = x.vals[1]
            if cap is None:
                cap = len(d)
            if len(d) > cap:
                raise Abort(f"Dict literal has {len(d)} entries but capacity is {cap}")
            r = DictV(d, cap)
            if groups and groups[0] and len(groups[0]) >= 2:
                r = I.coerce_coll(r, TName(["Dict"], [groups[0]]), "Dict", I.module_env)
            return r
        items = list(a)
        et = groups[0][0] if groups and groups[0] else None
        if et is not None and not isinstance(et, THole):
            items = [I.coerce(x, et, I.module_env) for x in items]
        if kind == "Set":
            d = {}
            for x in items:
                d[x] = True
            return SetV(d, cap if cap is not None else len(d))
        if kind == "List":
            if cap is None:
                cap = len(items)
            if len(items) > cap:
                raise Abort(f"List literal has {len(items)} elements but capacity is {cap}")
            return ListV(items, cap)
        return ArrayV(items, cap if cap is not None else len(items))
    return ctor


for _k in ("List", "Array", "Set", "Dict"):
    REG[_k] = (_coll_ctor(_k), "first", False)


@bi("MultiArray")
def b_multi(I, a, kw, ta):
    shape = [I.const_of(g, I.module_env) for g in ta[1]]
    fillv = a[0][1] if a and isinstance(a[0], tuple) else None
    n = 1
    for s in shape:
        n *= s
    return MultiV([fillv] * n, shape)


@bi("Range")
def b_range(I, a, kw, ta):
    r = a[0]
    step = a[1] if len(a) > 1 else 1
    return RangeV(r.start, r.limit, step, r.incl)


@bi("start")
def b_start(I, a, kw, ta):
    return a[0].start


@bi("limit")
def b_limit(I, a, kw, ta):
    return a[0].limit


@bi("step")
def b_step(I, a, kw, ta):
    return a[0].step


@bi("clone")
def b_clone(I, a, kw, ta):
    x = a[0]
    if isinstance(x, S_.ChanW):
        x.chan.wcount += 1
        return S_.ChanW(x.chan)
    if isinstance(x, S_.ChanR):
        x.chan.rcount += 1
        return S_.ChanR(x.chan)
    return x


@bi("close")
def b_close(I, a, kw, ta):
    x = a[0]
    if hasattr(x, "drop"):
        x.drop(I.sched)
    return UNIT


@bi("replace")
def b_replace(I, a, kw, ta):
    v, p, new = a
    if isinstance(p, PathV):
        return I.path_update(v, p.segs, lambda old: new)
    raise Abort("replace needs a data path")


@bi("modify", "first", True)
def b_modify(I, a, kw, ta):
    v, p, f = a
    if not isinstance(p, PathV):
        raise Abort("modify needs a data path")
    # evaluate f on the old leaf
    def get(v2, segs):
        for s in segs:
            v2 = I.field_get(v2, s)
        return v2
    old = get(v, p.segs)
    nv = yield from I.apply(f, [old])
    return I.path_update(v, p.segs, lambda o: nv)


def path_update(self, v, segs, fn):
    if not segs:
        return fn(v)
    s = segs[0]
    inner = self.field_get(v, s)
    new = self.path_update(inner, segs[1:], fn)
    return v.replace(s, new)


_I.path_update = path_update


# ---------------------------------------------------------------- functions
@bi("identity")
def b_identity(I, a, kw, ta):
    return a[0]


@bi("const")
def b_const(I, a, kw, ta):
    v = a[0]
    return Builtin(lambda I2, a2, kw2, ta2: v, "const")


@bi("flip")
def b_flip(I, a, kw, ta):
    f = a[0]
    return Builtin(lambda I2, a2, kw2, ta2: I2.apply(f, [a2[1], a2[0]]), "flip", gen=True)


def _curry(n):
    def curry(I, a, kw, ta):
        f = a[0]

        def build(got):
            def step(I2, a2, kw2, ta2):
                nxt = got + [a2[0]]
                if len(nxt) == n:
                    return I2.apply(f, nxt)
                return Done(build(nxt))
            return Builtin(step, "curried", gen=True)
        return build([])
    return curry


for _n in range(2, 7):
    REG[f"curry{_n}"] = (_curry(_n), "first", False)


@bi("uncurry")
def b_uncurry(I, a, kw, ta):
    """uncurry[n](g): the inverse of curry. g takes one argument and returns a function, n times over;
    the result takes all n arguments at once.  n is a constant in brackets, like round_to[n]."""
    if not ta:
        raise Abort("uncurry needs its number of parameters in brackets, as in uncurry[2](g)")
    n = I.run_sync(I.ev(ta[0][0].expr, I.module_env))
    if not isinstance(n, int) or isinstance(n, bool) or n < 2:
        raise Abort("uncurry[n] needs a constant n of 2 or more")
    g = a[0]

    def go(I2, a2, kw2, ta2):
        if len(a2) != n:
            raise Abort(f"this function was made by uncurry[{n}] and takes {n} arguments, not {len(a2)}")
        return _apply_chain(I2, g, list(a2))
    return Builtin(go, "uncurried", gen=True)


def _apply_chain(I, g, args):
    v = g
    for x in args:
        v = yield from I.apply(v, [x])
    return v


@bi("curry")
def b_curry(I, a, kw, ta):
    """curry(f): any number of parameters (two or more), read from f's declaration."""
    f = a[0]
    node = getattr(f, "node", None)
    if node is None:
        raise Abort("curry needs a declared function or a function literal")
    if node.__class__.__name__ == "FnGroup":
        node = node.clauses[0]
    ps = node.params or []
    if any(getattr(p, "mod", None) or getattr(p, "variadic", None) for p in ps):
        raise Abort("curry cannot take a function with a ref, lazy, using, or variadic parameter")
    if len(ps) < 2:
        raise Abort("curry needs a function of two or more parameters")
    return _curry(len(ps))(I, a, kw, ta)


# ---------------------------------------------------------------- assertions
@bi("assert")
def b_assert(I, a, kw, ta):
    if not a[0]:
        raise Abort("assertion failed")
    return UNIT


@bi("debug_assert")
def b_debug_assert(I, a, kw, ta):
    if CONTRACTS[0] and not a[0]:
        raise Abort("debug assertion failed")
    return UNIT


@bi("assert_eq")
def b_assert_eq(I, a, kw, ta):
    if not I.values_eq(a[0], a[1]):
        raise Abort(f"assert_eq failed: {show(a[0], I)} != {show(a[1], I)}")
    return UNIT


@bi("assert_ne")
def b_assert_ne(I, a, kw, ta):
    if I.values_eq(a[0], a[1]):
        raise Abort(f"assert_ne failed: both are {show(a[0], I)}")
    return UNIT


# ---------------------------------------------------------------- stream stages and terminals
def src_of(I, v):
    return make_iter(I, v)


def stage(name, pos, make):
    def f(I, a, kw, ta):
        return make(I, a)
    REG[name] = (f, pos, False)


stage("to_stream", "first", lambda I, a: stream_of(I, a[0]))
stage("map", "last", lambda I, a: _map(I, a))
stage("filter", "last", lambda I, a: StreamV(lambda: FilterIter(I, src_of(I, a[1]), a[0])))
stage("flat_map", "last", lambda I, a: StreamV(lambda: FlatMapIter(I, src_of(I, a[1]), a[0])))
stage("take", "last", lambda I, a: StreamV(lambda: TakeIter(I, src_of(I, a[1]), a[0])))
stage("drop", "last", lambda I, a: StreamV(lambda: DropIter(I, src_of(I, a[1]), a[0])))
stage("take_while", "last", lambda I, a: StreamV(lambda: TakeWhileIter(I, src_of(I, a[1]), a[0])))
stage("drop_while", "last", lambda I, a: StreamV(lambda: DropWhileIter(I, src_of(I, a[1]), a[0])))
stage("scan", "last", lambda I, a: StreamV(lambda: ScanIter(I, src_of(I, a[2]), a[0], a[1])))
stage("enumerate", "first", lambda I, a: StreamV(lambda: EnumerateIter(src_of(I, a[0]))))
stage("concat", "first", lambda I, a: StreamV(lambda: ConcatIter(src_of(I, a[0]), src_of(I, a[1]))))
stage("zip", "first", lambda I, a: StreamV(lambda: ZipIter(src_of(I, a[0]), src_of(I, a[1]))))


def _map(I, a):
    f, s = a[0], a[1]
    if isinstance(s, EnumV) or (not is_streamable(s) and I.find_method_for(s, "map")):
        return None
    return StreamV(lambda: MapIter(I, src_of(I, s), f))


def _map_dispatch(I, a, kw, ta):
    f, s = a[0], a[1]
    if isinstance(s, EnumV):
        m = I.find_method_for(s, "map")
        if m is not None:
            return I.apply_method(m, s, [f])
        if s.et is RESULT_T:
            return _res_map(I, f, s)
    if isinstance(s, (ListV, ArrayV)) and I.find_method_for(s, "map"):
        return I.apply_method(I.find_method_for(s, "map"), s, [f])
    return Done(StreamV(lambda: MapIter(I, src_of(I, s), f)))


def _res_map(I, f, r):
    if r.case == "Ok":
        v = yield from I.apply(f, [r.vals[0]])
        return Ok(v)
    return r


REG["map"] = (_map_dispatch, "last", True)


def _flat_map_dispatch(I, a, kw, ta):
    f, s = a[0], a[1]
    if isinstance(s, EnumV):
        m = I.find_method_for(s, "flat_map")
        if m is not None:
            return I.apply_method(m, s, [f])
        if s.et is RESULT_T:
            return _res_flat_map(I, f, s)
    if isinstance(s, (ListV, ArrayV)) and I.find_method_for(s, "flat_map"):
        return I.apply_method(I.find_method_for(s, "flat_map"), s, [f])
    return Done(StreamV(lambda: FlatMapIter(I, src_of(I, s), f)))


def _res_flat_map(I, f, r):
    if r.case == "Ok":
        return (yield from I.apply(f, [r.vals[0]]))
    return r


REG["flat_map"] = (_flat_map_dispatch, "last", True)


def buffered(name, pos, fnmaker):
    def f(I, a, kw, ta):
        src = a[-1] if pos == "last" else a[0]
        rest = a[:-1] if pos == "last" else a[1:]
        fn = fnmaker(I, rest)
        return StreamV(lambda: BufferIter(I, src_of(I, src), fn))
    REG[name] = (f, pos, False)


def _sort_fn(I, rest):
    def run(buf):
        keyf = functools_cmp(I)
        return Done(sorted(buf, key=cmp_to_key(keyf)))
    return run


def functools_cmp(I):
    def cmp(x, y):
        if lt(x, y):
            return -1
        if lt(y, x):
            return 1
        return 0
    return cmp


buffered("sort", "first", _sort_fn)


def _sort_by_fn(I, rest):
    keyf = rest[0]

    def run(buf):
        keys = []
        for x in buf:
            k = yield from I.apply(keyf, [x])
            keys.append(k)
        idx = sorted(range(len(buf)), key=cmp_to_key(lambda i, j: -1 if lt(keys[i], keys[j]) else (1 if lt(keys[j], keys[i]) else 0)))
        return [buf[i] for i in idx]
    return run


buffered("sort_by", "last", _sort_by_fn)
buffered("take_last", "last", lambda I, rest: (lambda buf: Done(buf[-rest[0]:] if rest[0] > 0 else [])))
buffered("reverse", "first", lambda I, rest: (lambda buf: Done(list(reversed(buf)))))


def _chunks_fn(I, rest):
    n = rest[0]
    return lambda buf: Done([ListV(buf[i:i + n], n) for i in range(0, len(buf), n)])


def _windows_fn(I, rest):
    n = rest[0]
    return lambda buf: Done([ListV(buf[i:i + n], n) for i in range(0, len(buf) - n + 1)])


buffered("chunks", "last", _chunks_fn)
buffered("windows", "last", _windows_fn)


@bi("unfold", "first")
def b_unfold(I, a, kw, ta):
    seed, f = a[0], a[1]
    return StreamV(lambda: UnfoldIter(I, seed, f))


@bi("repeat")
def b_repeat(I, a, kw, ta):
    v = a[0]

    class It:
        def nxt(self):
            return Done(v)
    return StreamV(lambda: It())


@bi("iterate", "first")
def b_iterate(I, a, kw, ta):
    seed, f = a

    class It:
        def __init__(self):
            self.cur = seed
            self.first = True

        def nxt(self):
            if self.first:
                self.first = False
                return Done(self.cur)
            return self._n()

        def _n(self):
            self.cur = yield from I.apply(f, [self.cur])
            return self.cur
    return StreamV(lambda: It())


@bi("Stream")
def b_Stream(I, a, kw, ta):
    src = a[0]
    if len(a) > 1 and isinstance(a[1], RangeV) and isinstance(src, (Seq,)):
        r = a[1]
        items = src.items
        s = r.start or 0
        e = len(items) if r.limit is None else (r.limit + 1 if r.incl else r.limit)
        return StreamV(lambda: ListIter(items[s:e]))
    return stream_of(I, src)


# terminals
@bi("reduce", "last", True)
def b_reduce(I, a, kw, ta):
    start, f, s = a[0], a[1], a[2]
    it = make_iter(I, s)
    acc = start
    while True:
        x = yield from it.nxt()
        if x is END:
            return acc
        acc = yield from I.apply(f, [acc, x])


@bi("collect", "first", True)
def b_collect(I, a, kw, ta):
    items = yield from drain(I, a[0])
    return ListV(items, max(len(items), 1) if False else len(items))


def _num_fold(I, s, op, init):
    items = yield from drain(I, s)
    acc = init
    for x in items:
        acc = arith(op, acc, x) if acc is not None else x
    return acc


@bi("sum", "first", True)
def b_sum(I, a, kw, ta):
    items = yield from drain(I, a[0])
    if not items:
        return 0
    acc = items[0]
    for x in items[1:]:
        acc = arith("+", acc, x)
    return acc


@bi("product", "first", True)
def b_product(I, a, kw, ta):
    items = yield from drain(I, a[0])
    if not items:
        return 1
    acc = items[0]
    for x in items[1:]:
        acc = arith("*", acc, x)
    return acc


@bi("count", "first", True)
def b_count(I, a, kw, ta):
    items = yield from drain(I, a[0])
    return len(items)


@bi("avg", "first", True)
def b_avg(I, a, kw, ta):
    items = yield from drain(I, a[0])
    return sum(items) / len(items)


@bi("any", "last", True)
def b_any(I, a, kw, ta):
    it = make_iter(I, a[1])
    while True:
        x = yield from it.nxt()
        if x is END:
            return False
        if (yield from I.apply(a[0], [x])):
            return True


@bi("all", "last", True)
def b_all(I, a, kw, ta):
    it = make_iter(I, a[1])
    while True:
        x = yield from it.nxt()
        if x is END:
            return True
        if not (yield from I.apply(a[0], [x])):
            return False


@bi("find", "last", True)
def b_find(I, a, kw, ta):
    it = make_iter(I, a[1])
    while True:
        x = yield from it.nxt()
        if x is END:
            return err_reserved("MISSING", "not found")
        if (yield from I.apply(a[0], [x])):
            return Ok(x)


@bi("first", "first", True)
def b_first(I, a, kw, ta):
    it = make_iter(I, a[0])
    x = yield from it.nxt()
    return err_reserved("MISSING", "empty") if x is END else Ok(x)


@bi("last", "first", True)
def b_last(I, a, kw, ta):
    items = yield from drain(I, a[0])
    return Ok(items[-1]) if items else err_reserved("MISSING", "empty")


@bi("partition", "last", True)
def b_partition(I, a, kw, ta):
    items = yield from drain(I, a[1])
    yes, no = [], []
    for x in items:
        (yes if (yield from I.apply(a[0], [x])) else no).append(x)
    return TupleV([ListV(yes), ListV(no)])


@bi("unzip", "first", True)
def b_unzip(I, a, kw, ta):
    items = yield from drain(I, a[0])
    return TupleV([ListV([t.vals[0] for t in items]), ListV([t.vals[1] for t in items])])


@bi("group_by", "last", True)
def b_group_by(I, a, kw, ta):
    items = yield from drain(I, a[1])
    d = {}
    for x in items:
        k = yield from I.apply(a[0], [x])
        d.setdefault(k, []).append(x)
    return DictV({k: ListV(v) for k, v in d.items()}, len(d))


@bi("traverse", "last", True)
def b_traverse(I, a, kw, ta):
    f, s = a[0], a[1]
    items = yield from drain(I, s)
    out = []
    for x in items:
        r = yield from I.apply(f, [x])
        if isinstance(r, EnumV) and (r.case in ("Err", "Nothing")):
            return r
        out.append(r.vals[0] if isinstance(r, EnumV) else r)
    return Ok(ListV(out))


@bi("sequence", "first", True)
def b_sequence(I, a, kw, ta):
    items = yield from drain(I, a[0])
    out = []
    for r in items:
        if isinstance(r, EnumV) and r.case in ("Err", "Nothing"):
            return r
        out.append(r.vals[0])
    return Ok(ListV(out))


# ---------------------------------------------------------------- concurrency
@bi("Ring")
def b_ring(I, a, kw, ta):
    if not GC[0]:
        raise Abort("`Ring` exists only in moxie/gc")
    n = a[0] if a else None
    if not isinstance(n, int) or n < 1:
        raise Abort("Ring needs a capacity of at least 1")
    return RingV([], n)


@bi("Atom")
def b_atom(I, a, kw, ta):
    v = a[0]
    if ta and ta[0]:
        v = I.coerce(v, ta[0][0], I.module_env)
    return S_.AtomV(v)


@bi("swap", "first", True)
def b_swap(I, a, kw, ta):
    at, f = a[0], a[1]
    nv = yield from I.apply(f, [at.atom_value])
    at.atom_value = nv
    return nv


@bi("reset")
def b_reset(I, a, kw, ta):
    a[0].atom_value = a[1]
    return a[1]


@bi("Chan")
def b_chan(I, a, kw, ta):
    cap = 0
    if ta and len(ta) > 1 and ta[1]:
        cap = I.const_of(ta[1][0], I.module_env)
        if isinstance(cap, Kw):
            if GC[0] and cap == "unbounded":
                cap = INF_CAP
            else:
                raise Abort(f"unknown channel capacity #{cap}" if GC[0] else "`#unbounded` exists only in moxie/gc")
        elif cap is None:
            cap = 0
        elif not isinstance(cap, int) or cap < 0:
            raise Abort("channel capacity must be a non-negative Int")
    ch = S_.Chan(cap)
    return TupleV([S_.ChanR(ch), S_.ChanW(ch)])


@bi("write", "first", True)
def b_write(I, a, kw, ta):
    return (yield from a[0].write(I, a[1]))


@bi("Future")
def b_future(I, a, kw, ta):
    st = S_.FutureState()
    return TupleV([S_.FutureR(st), S_.FutureW(st)])


@bi("resolve")
def b_resolve(I, a, kw, ta):
    w, v = a
    if w.st.state == "Pending":
        w.st.state = "Resolved"
        w.st.value = v
    w.dropped = True
    return UNIT


@bi("reject")
def b_reject(I, a, kw, ta):
    w, e = a
    if w.st.state == "Pending":
        w.st.state = "Rejected"
        w.st.value = e
    w.dropped = True
    return UNIT


@bi("Timer")
def b_timer(I, a, kw, ta):
    return S_.TimerV()


@bi("arm")
def b_arm(I, a, kw, ta):
    I.sched.arm_timer(a[0], a[1].ns)
    return UNIT


@bi("arm_every")
def b_arm_every(I, a, kw, ta):
    I.sched.arm_timer(a[0], a[1].ns, a[1].ns)
    return UNIT


@bi("disarm")
def b_disarm(I, a, kw, ta):
    I.sched.disarm(a[0])
    return UNIT


@bi("after")
def b_after(I, a, kw, ta):
    t = S_.TimerV()
    I.sched.arm_timer(t, a[0].ns)
    return t


@bi("sleep", "first", True)
def b_sleep(I, a, kw, ta):
    yield ("sleep", a[0].ns)
    return UNIT


@bi("transaction", "first", True)
def b_transaction(I, a, kw, ta):
    from .sqlrt import transaction
    return (yield from transaction(I, a, kw))


# ---------------------------------------------------------------- more stream helpers
class _DistinctIter:
    def __init__(self, src):
        self.src, self.seen = src, set()

    def nxt(self):
        while True:
            x = yield from self.src.nxt()
            if x is END:
                return END
            if x not in self.seen:
                self.seen.add(x)
                return x


class _FlattenIter:
    def __init__(self, I, src):
        self.I, self.src, self.cur = I, src, None

    def nxt(self):
        while True:
            if self.cur is not None:
                y = yield from self.cur.nxt()
                if y is not END:
                    return y
                self.cur = None
            x = yield from self.src.nxt()
            if x is END:
                return END
            self.cur = make_iter(self.I, x)


class _CycleIter:
    def __init__(self, I, src):
        self.I, self.src = I, src
        self.items, self.i, self.filled = [], 0, False

    def nxt(self):
        if not self.filled:
            x = yield from self.src.nxt()
            if x is not END:
                self.items.append(x)
                return x
            self.filled = True
        if not self.items:
            return END
        x = self.items[self.i % len(self.items)]
        self.i += 1
        return x


stage("distinct", "first", lambda I, a: StreamV(lambda: _DistinctIter(src_of(I, a[0]))))
stage("flatten", "first", lambda I, a: StreamV(lambda: _FlattenIter(I, src_of(I, a[0]))))
stage("cycle", "first", lambda I, a: StreamV(lambda: _CycleIter(I, src_of(I, a[0]))))


class _Intersperse:
    def __init__(self, src, sep):
        self.src, self.sep = src, sep
        self.state = 0      # 0 = before first, 1 = last was an element, 2 = a separator was just emitted
        self.held = None

    def nxt(self):
        if self.state == 2:
            self.state = 1
            return self.held
        x = yield from self.src.nxt()
        if x is END:
            return END
        if self.state == 0:
            self.state = 1
            return x
        self.held = x
        self.state = 2
        return self.sep


stage("intersperse", "last", lambda I, a: StreamV(lambda: _Intersperse(src_of(I, a[1]), a[0])))


@bi("zip_with", "last", True)
def b_zip_with(I, a, kw, ta):
    f = a[0]
    xs = make_iter(I, a[1])
    ys = make_iter(I, a[2])
    out = []
    while True:
        x = yield from xs.nxt()
        if x is END:
            break
        y = yield from ys.nxt()
        if y is END:
            break
        out.append((yield from I.apply(f, [x, y])))
    return StreamV(lambda: ListIter(out))


@bi("reduce_right", "last", True)
def b_reduce_right(I, a, kw, ta):
    start, f, s = a[0], a[1], a[2]
    items = yield from drain(I, s)
    acc = start
    for x in reversed(items):
        acc = yield from I.apply(f, [x, acc])
    return acc


def _by(which):
    def fn(I, a, kw, ta):
        key, s = a[0], a[1]
        items = yield from drain(I, s)
        if not items:
            return err_reserved("MISSING", "empty")
        best, bk = items[0], (yield from I.apply(key, [items[0]]))
        for x in items[1:]:
            k = yield from I.apply(key, [x])
            if (which == "min" and lt(k, bk)) or (which == "max" and lt(bk, k)):
                best, bk = x, k
        return Ok(best)
    return fn


REG["min_by"] = (_by("min"), "last", True)
REG["max_by"] = (_by("max"), "last", True)


@bi("span", "last", True)
def b_span(I, a, kw, ta):
    items = yield from drain(I, a[1])
    i = 0
    while i < len(items) and (yield from I.apply(a[0], [items[i]])):
        i += 1
    return TupleV([ListV(items[:i]), ListV(items[i:])])


@bi("split_at", "last", True)
def b_split_at(I, a, kw, ta):
    items = yield from drain(I, a[1])
    n = max(0, a[0])
    return TupleV([ListV(items[:n]), ListV(items[n:])])
