"""Packages that ship with the interpreter, written in moxie (moxie/std/).  A program's own files win over these.

`fp.state` is moxie/gc only: it needs closures that have one type per signature, which no-GC moxie does not give.
"""
import os

STD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "std")
GC_ONLY = {"fp.state", "fp.reader", "fp.writer", "fp.cont", "fp.free", "fp.trans"}


def find_std(parts):
    cands = [os.path.join(STD_DIR, *parts) + ".mxi", os.path.join(STD_DIR, *parts, parts[-1] + ".mxi")]
    return next((p for p in cands if os.path.exists(p)), None)


def gc_only(path, parts):
    """True when `path` is a built-in package that only moxie/gc has."""
    return path is not None and path.startswith(STD_DIR) and ".".join(parts) in GC_ONLY


def refusal(parts):
    return f"the package '{'.'.join(parts)}' is only in moxie/gc (run with --gc): it needs closures that have one type per signature"
