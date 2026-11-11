"""Runtime values for the Moxie interpreter."""
import struct
import math
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_UP, ROUND_DOWN, ROUND_CEILING, ROUND_FLOOR, localcontext


# moxie/gc mode: List, Set and Dict have no fixed capacity (set by `--gc` or MOXIE_GC=1)
import os as _os
GC = [bool(_os.environ.get("MOXIE_GC"))]
INF_CAP = 1 << 62
CONTRACTS = [True]    # False under --release: requires/ensures/invariant are not checked


# ---------------------------------------------------------------- exceptions
class Abort(Exception):
    """An unrecoverable fault: ends the fiber."""

    def __init__(self, msg, line=0):
        super().__init__(msg)
        self.msg = msg
        self.line = line


class BreakEx(Exception):
    def __init__(self, label=None, value=None, daemon=False):
        self.label = label
        self.value = value
        self.daemon = daemon


class ContinueEx(Exception):
    def __init__(self, label=None):
        self.label = label


class ReturnEx(Exception):
    def __init__(self, value):
        self.value = value


class Done:
    """An already-finished 'generator': `yield from Done(v)` gives v."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __iter__(self):
        return self

    def __next__(self):
        raise StopIteration(self.v)


# ---------------------------------------------------------------- small values
class UnitT:
    __slots__ = ()

    def __repr__(self):
        return "()"

    def __eq__(self, o):
        return isinstance(o, UnitT)

    def __hash__(self):
        return 0


UNIT = UnitT()


class Char(str):
    __slots__ = ()


class Kw(str):
    """A keyword literal such as #fast."""
    __slots__ = ()


class Dur:
    __slots__ = ("ns",)

    def __init__(self, ns):
        self.ns = ns

    def __eq__(self, o):
        return isinstance(o, Dur) and o.ns == self.ns

    def __hash__(self):
        return hash(self.ns)

    def __lt__(self, o):
        return self.ns < o.ns

    def __add__(self, o):
        return Dur(self.ns + o.ns)

    def __sub__(self, o):
        return Dur(self.ns - o.ns)


DUR_UNITS = {"ns": 1, "us": 1000, "ms": 1_000_000, "s": 1_000_000_000,
             "m": 60 * 1_000_000_000, "h": 3600 * 1_000_000_000}


# ---------------------------------------------------------------- numbers
class FixedInt(int):
    """Base for sized integers. Subclasses set bits, signed, tname."""
    bits = 64
    signed = True
    tname = "Int"

    @classmethod
    def lo(cls):
        return -(1 << (cls.bits - 1)) if cls.signed else 0

    @classmethod
    def hi(cls):
        return (1 << (cls.bits - 1)) - 1 if cls.signed else (1 << cls.bits) - 1

    @classmethod
    def fits(cls, v):
        return cls.lo() <= v <= cls.hi()

    @classmethod
    def make(cls, v):
        """Checked construction."""
        if not cls.fits(v):
            raise Abort(f"{cls.tname} overflow: {v} does not fit")
        return cls(v)

    @classmethod
    def wrap(cls, v):
        m = 1 << cls.bits
        v &= m - 1
        if cls.signed and v >= (1 << (cls.bits - 1)):
            v -= m
        return cls(v)

    def __repr__(self):
        return int.__repr__(self)

    def __hash__(self):
        return int.__hash__(self)


_INT_CLASSES = {}


def int_class(name, bits, signed):
    key = (bits, signed, name)
    c = _INT_CLASSES.get(key)
    if c is None:
        c = type(name, (FixedInt,), {"bits": bits, "signed": signed, "tname": name})
        _INT_CLASSES[key] = c
    return c


for _n, _b, _s in [("Int8", 8, True), ("Int16", 16, True), ("Int32", 32, True), ("Int64", 64, True),
                   ("UInt8", 8, False), ("UInt16", 16, False), ("UInt32", 32, False), ("UInt64", 64, False),
                   ("UInt", 64, False), ("Byte", 8, False)]:
    int_class(_n, _b, _s)
INT_CLASSES = {c.tname: c for c in _INT_CLASSES.values()}


def bigint_class(bits):
    return int_class(f"BigInt[{bits}]", bits, True)


INT_MIN = -(1 << 63)
INT_MAX = (1 << 63) - 1


def check_int(v):
    if v < INT_MIN or v > INT_MAX:
        raise Abort("Int overflow")
    return v


class F32(float):
    __slots__ = ()

    @staticmethod
    def of(v):
        try:
            return F32(struct.unpack("f", struct.pack("f", v))[0])
        except OverflowError:
            return F32(math.copysign(math.inf, v))


class Dec:
    """Exact decimal with a declared (digits, scale)."""
    __slots__ = ("v", "scale")

    def __init__(self, v, scale=None):
        self.v = v if isinstance(v, Decimal) else Decimal(v)
        self.scale = scale

    def __eq__(self, o):
        return isinstance(o, Dec) and self.v == o.v

    def __hash__(self):
        return hash(self.v)

    def __lt__(self, o):
        return self.v < o.v

    def __le__(self, o):
        return self.v <= o.v


def fmt_float(x):
    if x != x:
        return "NAN"
    if x == math.inf:
        return "INF"
    if x == -math.inf:
        return "-INF"
    if isinstance(x, F32):
        for p in range(1, 12):
            s = "%.*g" % (p, x)
            if struct.unpack("f", struct.pack("f", float(s)))[0] == float(x):
                break
        f = float(s)
        r = repr(f)
        return r
    r = repr(float(x))
    if r.endswith(".0") or "e" in r or "." in r:
        pass
    if "e" in r:
        mant, ex = r.split("e")
        ex = int(ex)
        r = f"{mant}e{ex}"
    return r


def fmt_dec(d):
    v = d.v
    if d.scale is not None:
        q = Decimal(1).scaleb(-d.scale)
        v = v.quantize(q)
    return format(v, "f")


# ---------------------------------------------------------------- composite values
class TupleV:
    __slots__ = ("tname", "vals", "names", "targs", "lazy")

    def __init__(self, vals, names=None, tname=None):
        self.vals = vals
        self.names = names
        self.tname = tname
        self.targs = None       # type arguments known when the value was built (a generic tuple built under a type hint)
        self.lazy = None        # values of `lazy property` members already computed for this value (a rebuilt tuple starts empty)

    def get(self, key):
        if isinstance(key, int):
            return self.vals[key]
        i = self.names.index(key)
        return self.vals[i]

    def has(self, key):
        return self.names is not None and key in self.names

    def __eq__(self, o):
        return (isinstance(o, TupleV) and o.tname == self.tname and o.vals == self.vals
                and (o.names == self.names or self.names is None or o.names is None))

    def __hash__(self):
        return hash((self.tname, tuple(self.vals)))

    def replace(self, key, val):
        vals = list(self.vals)
        if isinstance(key, int):
            vals[key] = val
        else:
            vals[self.names.index(key)] = val
        return TupleV(vals, self.names, self.tname)


class EnumType:
    def __init__(self, name):
        self.name = name
        self.cases = {}        # case name -> CaseInfo
        self.order = []
        self.header = None     # header field names
        self.derivs = []
        self.tparams = []


class CaseInfo:
    def __init__(self, name, index, fields, ftypes=None):
        self.name = name
        self.index = index
        self.fields = fields     # list of names (or None entries) ; [] for no payload
        self.ftypes = ftypes or []


class EnumV:
    __slots__ = ("et", "case", "vals", "names")

    def __init__(self, et, case, vals=(), names=None):
        self.et = et
        self.case = case
        self.vals = list(vals)
        self.names = names

    def __eq__(self, o):
        return isinstance(o, EnumV) and o.et is self.et and o.case == self.case and o.vals == self.vals

    def __hash__(self):
        return hash((self.et.name, self.case, tuple(self.vals)))

    def get(self, key):
        if isinstance(key, int):
            return self.vals[key]
        return self.vals[self.names.index(key)]


RESULT_T = EnumType("Result")
RESULT_T.order = ["Ok", "Err"]
RESULT_T.cases["Ok"] = CaseInfo("Ok", 0, ["value"])
RESULT_T.cases["Err"] = CaseInfo("Err", 1, ["error"])
FUTURE_T = EnumType("Future")
FUTURE_T.order = ["Pending", "Resolved", "Rejected"]
FUTURE_T.cases["Pending"] = CaseInfo("Pending", 0, [])
FUTURE_T.cases["Resolved"] = CaseInfo("Resolved", 1, ["value"])
FUTURE_T.cases["Rejected"] = CaseInfo("Rejected", 2, ["error"])


def Ok(v):
    return EnumV(RESULT_T, "Ok", [v], ["value"])


def Err(e):
    return EnumV(RESULT_T, "Err", [e], ["error"])


def is_ok(r):
    return isinstance(r, EnumV) and r.et is RESULT_T and r.case == "Ok"


def is_err(r):
    return isinstance(r, EnumV) and r.et is RESULT_T and r.case == "Err"


# Error codes
ERR_CODES = {"CLOSED": 1, "TOO_LONG": 2, "TOO_SHORT": 3, "MISSING": 4, "NO_SLOT": 5, "OUT_OF_RANGE": 6, "ABANDONED": 7, "BAD_ENCODING": 8, "NOT_FOUND": 9, "DENIED": 10, "IO_ERROR": 11, "TIMED_OUT": 12, "BAD_FORMAT": 13}
ERR_NAMES = {v: k for k, v in ERR_CODES.items()}


def make_error(code, msg):
    return TupleV([code, msg], ["code", "message"], "Error")


def err_reserved(name, msg=None):
    return Err(make_error(ERR_CODES[name], msg or name))


# collections
class Seq:
    """Base for Array, List, MultiArray element sequences."""
    __slots__ = ("items", "cap", "kind")

    def __init__(self, items, cap=None):
        self.items = items
        self.cap = cap if cap is not None else len(items)
        if GC[0] and self.kind == "List":
            self.cap = INF_CAP

    def __eq__(self, o):
        return type(o) is type(self) and o.items == self.items

    def __hash__(self):
        return hash(tuple(self.items))

    def __len__(self):
        return len(self.items)


class ArrayV(Seq):
    __slots__ = ()
    kind = "Array"


class ListV(Seq):
    __slots__ = ()
    kind = "List"


class RingV(Seq):
    """moxie/gc Ring[T](n): an immutable bounded buffer; adding to a full ring drops the oldest item."""
    __slots__ = ()
    kind = "Ring"


class SetV:
    __slots__ = ("items", "cap")
    kind = "Set"

    def __init__(self, items, cap=None):
        self.items = items         # python dict used as ordered set
        self.cap = INF_CAP if GC[0] else (cap if cap is not None else max(len(items), 0))

    def __eq__(self, o):
        return isinstance(o, SetV) and set(o.items) == set(self.items)

    def __hash__(self):
        return hash(frozenset(self.items))

    def __len__(self):
        return len(self.items)


class DictV:
    __slots__ = ("d", "cap")
    kind = "Dict"

    def __init__(self, d, cap=None):
        self.d = d
        self.cap = INF_CAP if GC[0] else (cap if cap is not None else len(d))

    def __eq__(self, o):
        return isinstance(o, DictV) and o.d == self.d

    def __hash__(self):
        return hash(tuple(self.d.items()))

    def __len__(self):
        return len(self.d)


class MultiV:
    """MultiArray: flat items with a shape."""
    __slots__ = ("items", "shape")
    kind = "MultiArray"

    def __init__(self, items, shape):
        self.items = items
        self.shape = tuple(shape)

    def __eq__(self, o):
        return isinstance(o, MultiV) and o.shape == self.shape and o.items == self.items

    def __hash__(self):
        return hash((self.shape, tuple(self.items)))

    def __len__(self):
        return len(self.items)


class RangeV:
    __slots__ = ("start", "limit", "step", "incl")

    def __init__(self, start, limit, step=1, incl=False):
        self.start = start
        self.limit = limit
        self.step = step
        self.incl = incl

    def __eq__(self, o):
        return (isinstance(o, RangeV) and (o.start, o.limit, o.step, o.incl) == (self.start, self.limit, self.step, self.incl))

    def __hash__(self):
        return hash((self.start, self.limit, self.step, self.incl))

    def values(self):
        s, l, st = self.start, self.limit, self.step
        if isinstance(s, Char):
            s, l = ord(s), (ord(l) if l is not None else None)
        out = []
        if l is None:
            raise Abort("cannot materialize an infinite range")
        if st > 0:
            end = l + 1 if self.incl else l
            v = s
            while v < end:
                out.append(v)
                v += st
        else:
            end = l - 1 if self.incl else l
            v = s
            while v > end:
                out.append(v)
                v += st
        return out


class Closure:
    __slots__ = ("node", "env", "name", "recv", "tparams", "bound", "impl", "owner", "iface_contracts")

    def __init__(self, node, env, name=None):
        self.node = node
        self.env = env
        self.name = name
        self.recv = None
        self.tparams = None
        self.bound = None
        self.impl = None
        self.owner = None
        self.iface_contracts = None


SUM_ELEM = {}      # id of a `sum`/`product` call node -> the element type's name, filled in by the checker


class Builtin:
    __slots__ = ("fn", "name", "gen", "pre")

    def __init__(self, fn, name, gen=False):
        self.fn = fn
        self.name = name
        self.gen = gen


class PartialV:
    """Pre-applied positional args (used for bound methods and pipe fills)."""
    __slots__ = ("fn", "pre", "post")

    def __init__(self, fn, pre, post=()):
        self.fn = fn
        self.pre = list(pre)
        self.post = list(post)


class ComposeV:
    __slots__ = ("fns",)

    def __init__(self, fns):
        self.fns = fns


class PathV:
    __slots__ = ("tname", "segs")

    def __init__(self, tname, segs):
        self.tname = tname
        self.segs = segs


class TypeV:
    """A type used as a value (for Planet.values(), Self, Box.Full ...)."""
    __slots__ = ("name", "info", "args")

    def __init__(self, name, info=None, args=None):
        self.name = name
        self.info = info
        self.args = args or []


class PkgV:
    __slots__ = ("name", "env", "internal")

    def __init__(self, name, env, internal=()):
        self.name = name
        self.env = env
        self.internal = internal
