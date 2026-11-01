"""Core helpers: environments, type names, equality, ordering, arithmetic, show/format."""
import math
import re
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_UP, ROUND_DOWN, ROUND_CEILING, ROUND_FLOOR
from .values import *   # noqa


# ---------------------------------------------------------------- environments
class Env:
    __slots__ = ("vars", "parent", "hidden", "recv", "usings", "func", "labels", "mod")

    def __init__(self, parent=None, hidden=False):
        self.vars = {}
        self.parent = parent
        self.hidden = hidden
        self.recv = None       # receiver value for method bodies
        self.usings = None
        self.func = parent.func if parent is not None else None   # FnCtx
        self.labels = None
        self.mod = parent.mod if parent is not None else None

    def lookup(self, name, interp=None):
        e = self
        while e is not None:
            v = e.vars.get(name, MISSING)
            if v is not MISSING:
                return v
            if e.recv is not None and interp is not None:
                r = interp.recv_member(e.recv, name)
                if r is not MISSING:
                    return r
            e = e.parent
        return MISSING

    def find_scope(self, name):
        e = self
        while e is not None:
            if name in e.vars:
                return e
            e = e.parent
        return None

    def bind(self, name, v):
        self.vars[name] = v

    def child(self, hidden=False):
        return Env(self, hidden)

    def names(self):
        out = {}
        e = self
        chain = []
        while e is not None:
            chain.append(e)
            e = e.parent
        for e in reversed(chain):
            out.update(e.vars)
        return out


class _Missing:
    def __repr__(self):
        return "MISSING"


MISSING = _Missing()


class FnCtx:
    __slots__ = ("name", "ret", "closure", "refs", "in_fiber", "is_entry")

    def __init__(self, name, ret=None, closure=None):
        self.name = name
        self.ret = ret
        self.closure = closure
        self.refs = None
        self.in_fiber = False
        self.is_entry = False


class ProgramExit(Exception):
    def __init__(self, code=0, msg=None):
        self.code = code
        self.msg = msg


# ---------------------------------------------------------------- type names
def type_name(v):
    t = type(v)
    if t is int:
        return "Int"
    if t is float:
        return "Double"
    if t is bool:
        return "Bool"
    if t is str:
        return "String"
    if isinstance(v, FixedInt):
        return v.tname
    if t is F32:
        return "Float"
    if t is Char:
        return "Char"
    if t is TupleV:
        return v.tname or "Tuple"
    if t is EnumV:
        return v.et.name
    if t is ListV:
        return "List"
    if t is ArrayV:
        return "Array"
    if t is SetV:
        return "Set"
    if t is DictV:
        return "Dict"
    if t is MultiV:
        return "MultiArray"
    if t is UnitT:
        return "Unit"
    if t is Kw:
        return "Keyword"
    if t is Dur:
        return "Duration"
    if t is Dec:
        return "Decimal"
    if t is RangeV:
        return "Range"
    if t is Closure or t is Builtin or t is PartialV or t is ComposeV or t is PathV:
        return "Function"
    n = getattr(v, "tname_", None)
    if n:
        return n
    return t.__name__


# ---------------------------------------------------------------- equality / ordering
def eq(a, b):
    if isinstance(a, float) or isinstance(b, float):
        try:
            return a == b
        except Exception:
            return False
    return a == b


def lt(a, b):
    ta = type(a)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a < b
    if isinstance(a, str) and isinstance(b, str):
        return a.encode("utf-8") < b.encode("utf-8")
    if isinstance(a, Dec):
        return a.v < b.v
    if isinstance(a, Dur):
        return a.ns < b.ns
    if isinstance(a, TupleV):
        for x, y in zip(a.vals, b.vals):
            if lt(x, y):
                return True
            if lt(y, x):
                return False
        return False
    if isinstance(a, EnumV):
        ia = a.et.cases[a.case].index
        ib = b.et.cases[b.case].index
        if ia != ib:
            return ia < ib
        for x, y in zip(a.vals, b.vals):
            if lt(x, y):
                return True
            if lt(y, x):
                return False
        return False
    if isinstance(a, Seq):
        for x, y in zip(a.items, b.items):
            if lt(x, y):
                return True
            if lt(y, x):
                return False
        return len(a.items) < len(b.items)
    if isinstance(a, bool):
        return a < b
    raise Abort(f"cannot order {type_name(a)} values")


# ---------------------------------------------------------------- arithmetic
def _promote(a, b):
    """Return (a, b, cls) where cls is the fixed-int class governing the operation, or None."""
    ca = a.__class__
    cb = b.__class__
    if ca is cb:
        return a, b, ca
    if isinstance(a, FixedInt) and cb is int:
        return a, b, ca
    if isinstance(b, FixedInt) and ca is int:
        return a, b, cb
    if isinstance(a, FixedInt) and isinstance(b, FixedInt):
        # widen to the larger class when mixing sized ints (implicit widening)
        return a, b, ca if ca.bits >= cb.bits else cb
    return a, b, None


def int_result(cls, v):
    if cls is int:
        if v < INT_MIN or v > INT_MAX:
            raise Abort("Int overflow")
        return v
    if not cls.fits(v):
        raise Abort(f"{cls.tname} overflow: {v} does not fit")
    return cls(v)


def idiv(a, b):
    if b == 0:
        raise Abort("division by zero")
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def imod(a, b):
    if b == 0:
        raise Abort("division by zero")
    return a - b * idiv(a, b)


def f32_result(x):
    return F32.of(x)


def arith(op, a, b):
    ta = a.__class__
    tb = b.__class__
    # plain ints (hot path)
    if ta is int and tb is int:
        if op == "+":
            r = a + b
        elif op == "-":
            r = a - b
        elif op == "*":
            r = a * b
        elif op == "/":
            r = idiv(a, b)
        elif op == "%":
            r = imod(a, b)
        elif op == "<<":
            if b < 0 or b >= 64:
                raise Abort("shift count out of range")
            r = a << b
            r = ((r + (1 << 63)) % (1 << 64)) - (1 << 63)
            return r
        elif op == ">>":
            if b < 0 or b >= 64:
                raise Abort("shift count out of range")
            return a >> b
        elif op == "&":
            return a & b
        elif op == "|":
            return a | b
        elif op == "^":
            return a ^ b
        else:
            raise Abort(f"bad operator {op}")
        if r < INT_MIN or r > INT_MAX:
            raise Abort("Int overflow")
        return r
    if ta is float and tb is float:
        return float_op(op, a, b, float)
    if isinstance(a, FixedInt) or isinstance(b, FixedInt):
        if isinstance(a, bool) or isinstance(b, bool):
            raise Abort("cannot do arithmetic on Bool")
        a, b, cls = _promote(a, b)
        if cls is None:
            raise Abort(f"cannot mix {type_name(a)} and {type_name(b)}")
        x, y = int(a), int(b)
        if op == "+":
            r = x + y
        elif op == "-":
            r = x - y
        elif op == "*":
            r = x * y
        elif op == "/":
            r = idiv(x, y)
        elif op == "%":
            r = imod(x, y)
        elif op == "&":
            return cls(x & y)
        elif op == "|":
            return cls(x | y)
        elif op == "^":
            return cls(x ^ y)
        elif op == "<<":
            if y < 0 or y >= cls.bits:
                raise Abort("shift count out of range")
            r = x << y
            return cls.wrap(r)
        elif op == ">>":
            if y < 0 or y >= cls.bits:
                raise Abort("shift count out of range")
            return cls(x >> y)
        else:
            raise Abort(f"bad operator {op}")
        return int_result(cls, r)
    if isinstance(a, float) or isinstance(b, float):
        if isinstance(a, F32) or isinstance(b, F32):
            return float_op(op, float(a), float(b), F32)
        return float_op(op, float(a), float(b), float)
    if isinstance(a, Dec) or isinstance(b, Dec):
        return dec_op(op, a, b)
    if isinstance(a, Dur) and isinstance(b, Dur):
        if op == "+":
            return Dur(a.ns + b.ns)
        if op == "-":
            return Dur(a.ns - b.ns)
    if isinstance(a, Dur) and isinstance(b, int):
        if op == "*":
            return Dur(a.ns * b)
        if op == "/":
            return Dur(idiv(a.ns, b))
    if isinstance(a, int) and isinstance(b, Dur) and op == "*":
        return Dur(a * b.ns)
    raise Abort(f"cannot apply '{op}' to {type_name(a)} and {type_name(b)}")


def float_op(op, x, y, cls):
    try:
        if op == "+":
            r = x + y
        elif op == "-":
            r = x - y
        elif op == "*":
            r = x * y
        elif op == "/":
            if y == 0:
                if x == 0 or x != x:
                    r = math.nan
                else:
                    neg = (math.copysign(1, x) < 0) != (math.copysign(1, y) < 0)
                    r = -math.inf if neg else math.inf
            else:
                r = x / y
        elif op == "%":
            r = math.fmod(x, y) if y != 0 else math.nan
        else:
            raise Abort(f"cannot apply '{op}' to floating-point numbers")
    except OverflowError:
        r = math.inf
    if cls is F32:
        return F32.of(r)
    return r


def to_dec(x):
    if isinstance(x, Dec):
        return x
    if isinstance(x, int):
        return Dec(Decimal(int(x)))
    raise Abort("cannot mix Decimal with a floating-point number")


def dec_op(op, a, b):
    a, b = to_dec(a), to_dec(b)
    scale = None
    if a.scale is not None and b.scale is not None:
        scale = max(a.scale, b.scale)
    else:
        scale = a.scale if a.scale is not None else b.scale
    if op == "+":
        return Dec(a.v + b.v, scale)
    if op == "-":
        return Dec(a.v - b.v, scale)
    if op == "*":
        s = None
        if a.scale is not None and b.scale is not None:
            s = a.scale + b.scale
        return Dec(a.v * b.v, s if s is not None else scale)
    raise Abort(f"cannot apply '{op}' to Decimal values (use div with a scale and rounding mode)")


def negate(a):
    if a.__class__ is int:
        if a == INT_MIN:
            raise Abort("Int overflow")
        return -a
    if isinstance(a, FixedInt):
        return int_result(a.__class__, -int(a))
    if isinstance(a, F32):
        return F32(-float(a))
    if isinstance(a, float):
        return -a
    if isinstance(a, Dec):
        return Dec(-a.v, a.scale)
    if isinstance(a, Dur):
        return Dur(-a.ns)
    raise Abort(f"cannot negate {type_name(a)}")


def bit_not(a):
    if isinstance(a, FixedInt):
        return a.__class__.wrap(~int(a))
    return ~a


# ---------------------------------------------------------------- show / display
def display(v, interp=None):
    """Text used by println and interpolation."""
    if v.__class__ is str or v.__class__ is Char:
        return v
    return show(v, interp)


ESCAPES = {"\n": "\\n", "\t": "\\t", "\\": "\\\\", '"': '\\"', "\r": "\\r", "$": "\\$"}


def quote_str(s):
    return '"' + "".join(ESCAPES.get(c, c) for c in s) + '"'


def show(v, interp=None):
    t = v.__class__
    if t is str:
        return quote_str(v)
    if t is int:
        return str(v)
    if t is bool:
        return "true" if v else "false"
    if t is float or t is F32:
        return fmt_float(v)
    if isinstance(v, FixedInt):
        return int.__repr__(v)
    if t is UnitT:
        return "()"
    if t is Char:
        return "'" + ESCAPES.get(str(v), str(v)).replace('"', '"') + "'" if False else "'" + {"\n": "\\n", "\t": "\\t", "\\": "\\\\", "'": "\\'"}.get(str(v), str(v)) + "'"
    if t is Kw:
        return "#" + str(v)
    if t is Dur:
        return fmt_dur(v)
    if t is Dec:
        return fmt_dec(v)
    if t is TupleV:
        if interp is not None and v.tname:
            s = interp.try_user_show(v)
            if s is not None:
                return s
        inner = []
        if v.names:
            for n, x in zip(v.names, v.vals):
                if interp is not None and v.tname and interp.has_delegate(v.tname, n):
                    x = interp.delegate_get_sync(x)
                inner.append(f"{n}: {show(x, interp)}")
        else:
            inner = [show(x, interp) for x in v.vals]
        if v.tname:
            return f"{v.tname}({', '.join(inner)})"
        return f"({', '.join(inner)})"
    if t is EnumV:
        if interp is not None:
            s = interp.try_user_show(v)
            if s is not None:
                return s
        if v.et.name == "Result":
            return f"{v.case}({show(v.vals[0], interp)})"
        if not v.vals:
            return f"{v.et.name}.{v.case}"
        inner = ", ".join(show(x, interp) for x in v.vals)
        return f"{v.et.name}.{v.case}({inner})"
    if t is ListV:
        return "List(" + ", ".join(show(x, interp) for x in v.items) + ")"
    if t is ArrayV:
        return "Array(" + ", ".join(show(x, interp) for x in v.items) + ")"
    if t is SetV:
        return "Set(" + ", ".join(show(x, interp) for x in v.items) + ")"
    if t is DictV:
        return "Dict(" + ", ".join(f"{show(k, interp)}: {show(x, interp)}" for k, x in v.d.items()) + ")"
    if t is MultiV:
        return "MultiArray(" + ", ".join(show(x, interp) for x in v.items) + ")"
    if t is RangeV:
        s = "" if v.start is None else show_plain(v.start)
        e = "" if v.limit is None else show_plain(v.limit)
        return f"{s}..{'=' if v.incl else ''}{e}"
    if t is Closure or t is Builtin or t is PartialV or t is ComposeV:
        return "<function>"
    if t is PathV:
        return "/" + v.tname + "".join("/" + str(s) for s in v.segs)
    if t is TypeV:
        return v.name
    return str(v)


def show_plain(v):
    return show(v)


def fmt_dur(d):
    ns = d.ns
    for unit in ("h", "m", "s", "ms", "us"):
        u = DUR_UNITS[unit]
        if ns != 0 and ns % u == 0:
            return f"{ns // u}{unit}"
    return f"{ns}ns"


# ---------------------------------------------------------------- format specs
SPEC_RE = re.compile(r"^(?:(.)?([<>^]))?([+\- ])?(#)?(0)?(\d+)?(,)?(?:\.(\d+))?([dxXobfeE%ns])?$", re.S)


def apply_spec(v, spec, interp=None, locale=None):
    # the Spec writes the locale type as `n.2f` (n, then precision and f); the grammar says `.2n`
    spec = re.sub(r"^(.*?)n(\.\d+)?f$", lambda mm: mm.group(1) + (mm.group(2) or "") + "n", spec)
    m = SPEC_RE.match(spec)
    if not m:
        raise Abort(f"bad format spec '{spec}'")
    fill, align, sign, alt, zero, width, comma, prec, typ = m.groups()
    width = int(width) if width else 0
    prec = int(prec) if prec is not None else None
    is_str = isinstance(v, str) and not isinstance(v, (Char, Kw))
    if typ in ("d", "x", "X", "o", "b"):
        n = int(v)
        if typ == "d":
            body = f"{abs(n):,}" if comma else str(abs(n))
        elif typ == "x":
            body = format(abs(n), "x")
        elif typ == "X":
            body = format(abs(n), "X")
        elif typ == "o":
            body = format(abs(n), "o")
        else:
            body = format(abs(n), "b")
        prefix = ""
        if alt:
            prefix = {"x": "0x", "X": "0X", "o": "0o", "b": "0b"}.get(typ, "")
        sgn = "-" if n < 0 else ("+" if sign == "+" else (" " if sign == " " else ""))
        return pad_num(sgn, prefix, body, width, fill, align, zero)
    if typ in ("f", "e", "E", "%", "n") or (typ is None and isinstance(v, (float, Dec)) and prec is not None):
        if isinstance(v, Dec):
            x = v.v
        else:
            x = float(v)
        if typ == "n":
            return format_locale(x, prec, locale, width, fill, align, zero, sign)
        p = 6 if prec is None else prec
        if typ == "%":
            body = f"{abs(x) * 100:,.{p}f}" if comma else f"{abs(x) * 100:.{p}f}"
            body += "%"
        elif typ in ("e", "E"):
            body = f"{abs(x):.{p}{typ}}"
        else:
            body = f"{abs(x):,.{p}f}" if comma else f"{abs(x):.{p}f}"
        neg = x < 0
        sgn = "-" if neg else ("+" if sign == "+" else (" " if sign == " " else ""))
        return pad_num(sgn, "", body, width, fill, align, zero)
    if isinstance(v, int) and not isinstance(v, bool) and typ is None:
        n = int(v)
        body = f"{abs(n):,}" if comma else str(abs(n))
        sgn = "-" if n < 0 else ("+" if sign == "+" else (" " if sign == " " else ""))
        return pad_num(sgn, "", body, width, fill, align, zero)
    text = display(v, interp)
    if prec is not None and is_str:
        text = text[:prec]
    return pad_text(text, width, fill, align or "<")


def pad_text(text, width, fill, align):
    n = len(text)
    if n >= width:
        return text
    fill = fill or " "
    extra = width - n
    if align == "<":
        return text + fill * extra
    if align == ">":
        return fill * extra + text
    left = extra // 2
    return fill * left + text + fill * (extra - left)


def pad_num(sgn, prefix, body, width, fill, align, zero):
    if zero and not align:
        total = len(sgn) + len(prefix) + len(body)
        if total < width:
            body = "0" * (width - total) + body
        return sgn + prefix + body
    return pad_text(sgn + prefix + body, width, fill, align or ">")


def format_locale(x, prec, locale, width, fill, align, zero, sign):
    if locale is None:
        raise Abort("format type 'n' needs a Locale in scope (using)")
    gs = locale.get("group", ",")
    ds = locale.get("decimal", ".")
    p = 6 if prec is None else prec
    s = f"{abs(x):,.{p}f}"
    s = s.replace(",", "\0").replace(".", ds).replace("\0", gs)
    sgn = "-" if x < 0 else ("+" if sign == "+" else "")
    return pad_num(sgn, "", s, width, fill, align, zero)


# ---------------------------------------------------------------- rounding
ROUNDING = {
    "half_even": ROUND_HALF_EVEN, "half_up": ROUND_HALF_UP, "half_down": ROUND_HALF_DOWN,
    "up": ROUND_UP, "down": ROUND_DOWN, "ceiling": ROUND_CEILING, "floor": ROUND_FLOOR,
}
