"""Streams: lazy, pull-based, element-at-a-time (recipes that rerun per terminal)."""
from .values import *   # noqa
from .core import *   # noqa
from .calls import END


class StreamV:
    __slots__ = ("opener",)
    tname_ = "Stream"

    def __init__(self, opener):
        self.opener = opener

    def open(self):
        return self.opener()


def is_streamable(v):
    return isinstance(v, (Seq, SetV, DictV, RangeV, StreamV, MultiV, str)) or hasattr(v, "chan_read")


def stream_of(I, v):
    """Turn a collection, range, channel end or stream into a StreamV."""
    if isinstance(v, StreamV):
        return v
    return StreamV(lambda: make_iter(I, v))


def make_iter(I, v):
    if isinstance(v, (ListV, ArrayV, RingV)):
        return ListIter(v.items)
    if isinstance(v, MultiV):
        return ListIter(v.items)
    if isinstance(v, SetV):
        return ListIter(list(v.items))
    if isinstance(v, DictV):
        return ListIter([TupleV([k, x]) for k, x in v.d.items()])
    if isinstance(v, RangeV):
        return RangeIter(v)
    if isinstance(v, StreamV):
        return v.open()
    if isinstance(v, str):
        return ListIter([Char(c) for c in v])
    if hasattr(v, "chan_read"):
        return ChanIter(I, v)
    if isinstance(v, EnumV) and v.et is RESULT_T:
        return ListIter([v.vals[0]] if v.case == "Ok" else [])
    raise Abort(f"cannot iterate over {type_name(v)}")


class ListIter:
    __slots__ = ("items", "i")

    def __init__(self, items):
        self.items = items
        self.i = 0

    def nxt(self):
        i = self.i
        if i < len(self.items):
            self.i = i + 1
            return Done(self.items[i])
        return Done(END)


class RangeIter:
    __slots__ = ("cur", "r", "ch")

    def __init__(self, r):
        self.r = r
        s = r.start
        self.ch = isinstance(s, Char)
        self.cur = ord(s) if self.ch else (s if s is not None else 0)

    def nxt(self):
        r = self.r
        v = self.cur
        lim = r.limit
        if self.ch and lim is not None:
            lim = ord(lim)
        if lim is not None:
            if r.step > 0:
                if (v > lim) if r.incl else (v >= lim):
                    return Done(END)
            else:
                if (v < lim) if r.incl else (v <= lim):
                    return Done(END)
        self.cur = v + r.step
        if self.ch:
            return Done(Char(chr(v)))
        if isinstance(r.start, FixedInt):
            return Done(r.start.__class__(v))
        return Done(v)


class ChanIter:
    def __init__(self, I, ch):
        self.I = I
        self.ch = ch

    def nxt(self):
        r = yield from self.ch.chan_read(self.I)
        if r.case == "Ok":
            return r.vals[0]
        return END


def drain(I, v):
    """Collect every element of a source into a Python list."""
    if isinstance(v, (ListV, ArrayV, RingV)):
        return Done(list(v.items))
    return _drain(I, v)


def _drain(I, v):
    it = make_iter(I, v)
    out = []
    while True:
        x = yield from it.nxt()
        if x is END:
            break
        out.append(x)
    return out


# ---------------------------------------------------------------- stages
class MapIter:
    def __init__(self, I, src, f):
        self.I, self.src, self.f = I, src, f

    def nxt(self):
        x = yield from self.src.nxt()
        if x is END:
            return END
        return (yield from self.I.apply(self.f, [x]))


class FilterIter:
    def __init__(self, I, src, f):
        self.I, self.src, self.f = I, src, f

    def nxt(self):
        while True:
            x = yield from self.src.nxt()
            if x is END:
                return END
            ok = yield from self.I.apply(self.f, [x])
            if ok:
                return x


class FlatMapIter:
    def __init__(self, I, src, f):
        self.I, self.src, self.f = I, src, f
        self.cur = None

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
            r = yield from self.I.apply(self.f, [x])
            self.cur = make_iter(self.I, r)


class TakeIter:
    def __init__(self, I, src, n):
        self.I, self.src, self.n = I, src, n
        self.k = 0

    def nxt(self):
        if self.k >= self.n:
            return END
        self.k += 1
        return (yield from self.src.nxt())


class DropIter:
    def __init__(self, I, src, n):
        self.I, self.src, self.n = I, src, n
        self.done = False

    def nxt(self):
        if not self.done:
            self.done = True
            for _ in range(self.n):
                x = yield from self.src.nxt()
                if x is END:
                    return END
        return (yield from self.src.nxt())


class TakeWhileIter:
    def __init__(self, I, src, f):
        self.I, self.src, self.f = I, src, f
        self.fin = False

    def nxt(self):
        if self.fin:
            return END
        x = yield from self.src.nxt()
        if x is END:
            return END
        ok = yield from self.I.apply(self.f, [x])
        if not ok:
            self.fin = True
            return END
        return x


class DropWhileIter:
    def __init__(self, I, src, f):
        self.I, self.src, self.f = I, src, f
        self.dropping = True

    def nxt(self):
        while True:
            x = yield from self.src.nxt()
            if x is END:
                return END
            if self.dropping:
                ok = yield from self.I.apply(self.f, [x])
                if ok:
                    continue
                self.dropping = False
            return x


class ScanIter:
    def __init__(self, I, src, start, f):
        self.I, self.src, self.f = I, src, f
        self.acc = start

    def nxt(self):
        x = yield from self.src.nxt()
        if x is END:
            return END
        self.acc = yield from self.I.apply(self.f, [self.acc, x])
        return self.acc


class EnumerateIter:
    def __init__(self, src):
        self.src = src
        self.i = 0

    def nxt(self):
        x = yield from self.src.nxt()
        if x is END:
            return END
        i = self.i
        self.i += 1
        return TupleV([i, x])


class ConcatIter:
    def __init__(self, a, b):
        self.a, self.b = a, b
        self.first = True

    def nxt(self):
        if self.first:
            x = yield from self.a.nxt()
            if x is not END:
                return x
            self.first = False
        return (yield from self.b.nxt())


class ZipIter:
    def __init__(self, a, b):
        self.a, self.b = a, b

    def nxt(self):
        x = yield from self.a.nxt()
        if x is END:
            return END
        y = yield from self.b.nxt()
        if y is END:
            return END
        return TupleV([x, y])


class BufferIter:
    """A vertical stage: drains the source, transforms the list, then replays it."""

    def __init__(self, I, src, fn):
        self.I, self.src, self.fn = I, src, fn
        self.items = None
        self.i = 0

    def nxt(self):
        if self.items is None:
            buf = []
            while True:
                x = yield from self.src.nxt()
                if x is END:
                    break
                buf.append(x)
            self.items = yield from self.fn(buf)
        if self.i < len(self.items):
            self.i += 1
            return self.items[self.i - 1]
        return END


class UnfoldIter:
    def __init__(self, I, seed, f):
        self.I, self.state, self.f = I, seed, f
        self.done = False

    def nxt(self):
        if self.done:
            return END
        r = yield from self.I.apply(self.f, [self.state])
        if isinstance(r, EnumV) and r.et is RESULT_T and r.case == "Ok":
            tv = r.vals[0]
            self.state = tv.vals[1]
            return tv.vals[0]
        self.done = True
        return END


class CallbackIter:
    """Iterator driven by a Python generator function: gen() yields via `yield from`."""
    pass
