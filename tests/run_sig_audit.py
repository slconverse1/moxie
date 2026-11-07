"""Every call of a library function written in the docs has no more arguments than the signature table allows
(a call with named options or placeholders, and examples of user functions, are skipped).  Run: python3 tests/run_sig_audit.py"""
import re, sys, glob, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from moxie.check import Checker

sg = Checker(()).load_sigs()
maxar = {k: max(len(x[1]) for x in v) for k, v in sg.items()}
USER_EXAMPLES = {"first", "show"}   # examples of user functions that reuse a library name


def top_args(s):
    depth, n, inq = 0, 0, None
    for ch in s:
        if inq:
            if ch == inq:
                inq = None
            continue
        if ch in "\"'":
            inq = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            n += 1
    return (n + 1) if s.strip() else 0


bad = []
for f in sorted(glob.glob("docs/*.md") + glob.glob("docs/gc/*.md")):
    t = open(f).read()
    for m in re.finditer(r'(?<![\w.])([a-z_][a-z0-9_]*)\(((?:[^()\n]|\([^()\n]*\))*)\)', t):
        name, args = m.group(1), m.group(2)
        if name not in maxar or name in USER_EXAMPLES:
            continue
        if re.search(r'(^|,)\s*\w+:(\s|$)', args) or re.search(r'\b_\d\b', args):
            continue
        if top_args(args) > maxar[name]:
            bad.append((f, m.group(0)[:80], top_args(args), maxar[name]))
for f, s, k, mx in bad:
    print("FAIL", f, s, f"{k} arguments, table allows {mx}")
print("sig audit: FAIL" if bad else f"sig audit: ok ({len(maxar)} functions)")
