"""The pool header at start-up (Spec section 3a, "Startup sequence").

`moxie pools FILE --header OUT` writes the header: how many of each counted resource the program can have open, the
largest number of fibers, and a hash of the program text.  `moxie --header=OUT run FILE` (or `[pools] header` in
Moxie.toml) reads it before the first line runs: a header made for other source text is refused, the memory the fibers
need is checked against the manifest's `[program] memory`, and the pools and the fiber count are then held to the
header's numbers.  With `[program] memory` set and no header file, the numbers come from the tally of the program.
"""
import json
import os

from .manifest import parse_size


class HeaderError(Exception):
    pass


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            h = json.load(f)
    except OSError as e:
        raise HeaderError(f"cannot read the pool header {path}: {e.strerror}")
    except ValueError as e:
        raise HeaderError(f"{path}: not a pool header ({e})")
    ok = (isinstance(h, dict) and isinstance(h.get("pools"), dict) and isinstance(h.get("fibers"), dict)
          and h.get("version") == 1 and "largest" in h["fibers"]
          and all(v is None or (isinstance(v, int) and not isinstance(v, bool) and v >= 0) for v in h["pools"].values())
          and (h["fibers"]["largest"] is None or isinstance(h["fibers"]["largest"], int)))
    if not ok:
        raise HeaderError(f"{path}: not a pool header (expected version 1 with pools and fibers)")
    return h


def budget_error(header, manifest):
    """The refusal message when the fibers cannot fit in `[program] memory`, else None."""
    total = parse_size(manifest.get("program", {}).get("memory"))
    if total is None:
        return None
    fib = manifest.get("fibers", {})
    mem, stack = parse_size(fib.get("memory")), parse_size(fib.get("stack"))
    n = header["fibers"]["largest"]
    if n is None:
        return ("[program] memory is set, but the largest number of fibers is not known: "
                "a fiber function has no limit (add fiber[n] or [fibers] limit)")
    if mem is None or stack is None:
        return "[program] memory is set, so [fibers] needs both memory and stack to say what one fiber uses"
    need = n * (mem + stack)
    if need > total:
        return f"the program needs {need} bytes ({n} fibers of {mem} memory + {stack} stack) but [program] memory is {total}"
    return None


def prepare(I, src, name, manifest, header_flag=None):
    """Run before the entry file: check the header and the budget, then hold the pools and fibers to the header."""
    from .values import GC
    path = header_flag
    if GC[0]:
        if path is not None or manifest.get("program", {}).get("memory") is not None:
            raise HeaderError("a pool header and [program] memory belong to moxie without a collector; moxie/gc has neither")
        return
    if path is None and manifest.get("pools", {}).get("header"):
        path = os.path.join(os.path.dirname(manifest["path"]), manifest["pools"]["header"])
    wants_budget = manifest.get("program", {}).get("memory") is not None
    if path is None and not wants_budget:
        return
    from .lexer import MoxieSyntaxError
    from .tally import Tally, header_dict, program_hash
    try:
        prog = I.load_source(src, name)
    except MoxieSyntaxError:
        return                                  # the run reports the syntax error
    if path is not None:
        header = load(path)
        if header.get("program") != program_hash(src):
            raise HeaderError(f"{path} was made for other source text; rebuild it with `moxie pools {name} --header {path}`")
    else:
        t = Tally(prog, manifest.get("fibers", {}).get("limit"))
        header = header_dict(t, t.program(), src)
    msg = budget_error(header, manifest)
    if msg:
        raise HeaderError(msg)
    if path is not None:
        I.pools.caps = {k: v for k, v in header["pools"].items() if v is not None}
        I.sched.fiber_cap = header["fibers"]["largest"]
