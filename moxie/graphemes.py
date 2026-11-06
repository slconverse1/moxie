"""Grapheme clusters: what a person sees as one character (Unicode UAX #29, extended clusters).

Python has no grapheme segmentation, so this applies the standard's break rules to properties worked out
from `unicodedata`.  Extended_Pictographic is approximated by the emoji blocks.
"""
import unicodedata

CR, LF, CONTROL, EXTEND, ZWJ, RI, SPACING, L, V, T, LV, LVT, PICT, OTHER = range(14)


def _pictographic(cp):
    return (0x1F300 <= cp <= 0x1FAFF or 0x1F000 <= cp <= 0x1F2FF or 0x2600 <= cp <= 0x27BF
            or 0x2B05 <= cp <= 0x2B55 or 0x231A <= cp <= 0x23FF or 0x2190 <= cp <= 0x21FF
            or cp in (0xA9, 0xAE, 0x203C, 0x2049, 0x2122, 0x2139, 0x24C2, 0x3030, 0x303D, 0x3297, 0x3299)
            or 0x25AA <= cp <= 0x25FE)


def kind(ch):
    cp = ord(ch)
    if cp == 0x0D:
        return CR
    if cp == 0x0A:
        return LF
    if cp == 0x200D:
        return ZWJ
    if cp == 0x200C or 0x1F3FB <= cp <= 0x1F3FF or 0xE0020 <= cp <= 0xE007F:
        return EXTEND
    if 0x1F1E6 <= cp <= 0x1F1FF:
        return RI
    if 0x1100 <= cp <= 0x115F or 0xA960 <= cp <= 0xA97C:
        return L
    if 0x1160 <= cp <= 0x11A7 or 0xD7B0 <= cp <= 0xD7C6:
        return V
    if 0x11A8 <= cp <= 0x11FF or 0xD7CB <= cp <= 0xD7FB:
        return T
    if 0xAC00 <= cp <= 0xD7A3:
        return LV if (cp - 0xAC00) % 28 == 0 else LVT
    cat = unicodedata.category(ch)
    if cat in ("Mn", "Me"):
        return EXTEND
    if cat == "Mc":
        return SPACING
    if cat in ("Cc", "Zl", "Zp") or (cat == "Cf" and cp not in (0x200C, 0x200D)):
        return CONTROL
    if _pictographic(cp):
        return PICT
    return OTHER


def split(s):
    """The extended grapheme clusters of `s`, in order."""
    out, start, n = [], 0, len(s)
    if n == 0:
        return out
    ks = [kind(c) for c in s]
    ri_run = 1 if ks[0] == RI else 0
    pict_ext = ks[0] == PICT          # inside "PICT Extend* ZWJ" so far: a following PICT joins
    for i in range(1, n):
        a, b = ks[i - 1], ks[i]
        join = False
        if a == CR and b == LF:
            join = True
        elif a in (CR, LF, CONTROL) or b in (CR, LF, CONTROL):
            join = False
        elif a == L and b in (L, V, LV, LVT):
            join = True
        elif a in (LV, V) and b in (V, T):
            join = True
        elif a in (LVT, T) and b == T:
            join = True
        elif b in (EXTEND, ZWJ, SPACING):
            join = True
        elif a == ZWJ and b == PICT and pict_ext:
            join = True
        elif a == RI and b == RI and ri_run % 2 == 1:
            join = True
        if not join:
            out.append(s[start:i])
            start = i
            ri_run = 0
            pict_ext = False
        # bookkeeping for the next step
        if b == RI:
            ri_run += 1
        else:
            ri_run = 0
        if b == PICT and not join:
            pict_ext = True
        elif b in (EXTEND, ZWJ) and pict_ext:
            pass
        elif b == PICT and join:
            pict_ext = True
        else:
            pict_ext = False
    out.append(s[start:])
    return out
