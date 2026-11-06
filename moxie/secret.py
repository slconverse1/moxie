"""Secret[T]: a value that must never end up in a log or a message by accident (Spec section 5).

`secret(x)` wraps a value.  Showing it, interpolating it, printing it, or `dbg`-ing it gives `Secret(***)`.
`reveal(s)` is the only way to the value, so every use of the real thing is visible in the source.
`==`, ordering, and use as a Dict key are refused (a timing leak waiting to happen); `secret_eq(a, b)` compares
in constant time.
"""
import hmac
from .values import *   # noqa
from .prelude import bi


class SecretV:
    tname_ = "Secret"
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Secret(***)"

    __repr__ = __str__

    def __eq__(self, other):
        raise Abort("a Secret can't be compared with ==; use secret_eq(a, b)")

    __ne__ = __lt__ = __le__ = __gt__ = __ge__ = __eq__

    def __hash__(self):
        raise Abort("a Secret can't be a Dict key or Set member")


def _bytes(v):
    if isinstance(v, str):
        return v.encode("utf-8")
    if isinstance(v, (bytes, bytearray)):
        return bytes(v)
    if isinstance(v, ArrayV):
        return bytes(int(x) for x in v.items)
    return None


@bi("secret")
def b_secret(I, a, kw, ta):
    v = a[0]
    if isinstance(v, SecretV):
        return v
    if ta and ta[0]:
        v = I.coerce(v, ta[0][0], I.module_env)
    return SecretV(v)


@bi("reveal")
def b_reveal(I, a, kw, ta):
    s = a[0]
    if not isinstance(s, SecretV):
        raise Abort("reveal needs a Secret")
    return s.value


@bi("secret_eq")
def b_secret_eq(I, a, kw, ta):
    x, y = a[0], a[1]
    if not isinstance(x, SecretV) or not isinstance(y, SecretV):
        raise Abort("secret_eq compares two Secrets")
    bx, by = _bytes(x.value), _bytes(y.value)
    if bx is not None and by is not None:
        return hmac.compare_digest(bx, by)
    return x.value == y.value
