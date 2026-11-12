"""Unreachable `when` arms are a warning.  Run: python3 tests/run_unreachable.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def check(src):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "check", f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
WARN = [
 ("an arm after _", 'fn f(n Int) Int\n  when n\n    _ -> 1\n    2 -> 2\n', "can never run"),
 ("an arm after a bare name", 'fn f(n Int) Int\n  when n\n    x -> x\n    2 -> 2\n', "can never run"),
 ("a repeated literal", 'fn f(n Int) Int\n  when n\n    1 -> 1\n    1 -> 2\n    else 3\n', "repeats the one at line 3"),
 ("a repeated enum case", 'enum C\n  Red\n  Green\nfn f(c C) Int\n  when c\n    Red -> 1\n    Red -> 2\n    Green -> 3\n', "repeats the one at line 6"),
 ("a repeated case with a binding", 'enum C\n  Red\n  Blue(n Int)\nfn f(c C) Int\n  when c\n    Red -> 1\n    Blue(n) -> n\n    Blue(m) -> m\n', "repeats the one"),
 ("a repeated string", 'fn f(s String) Int\n  when s\n    "a" -> 1\n    "a" -> 2\n    else 3\n', "repeats the one"),
]
QUIET = [
 ("distinct literals and else", 'fn f(n Int) Int\n  when n\n    1 -> 1\n    2 -> 2\n    else 3\n'),
 ("enum cases", 'enum C\n  Red\n  Green\nfn f(c C) Int\n  when c\n    Red -> 1\n    Green -> 2\n'),
 ("a guarded bare name then more arms", 'fn f(n Int) Int\n  when n\n    x if x > 5 -> 1\n    2 -> 2\n    else 3\n'),
 ("a case with a literal inside, then the general one", 'enum C\n  Red\n  Blue(n Int)\nfn f(c C) Int\n  when c\n    Red -> 1\n    Blue(1) -> 5\n    Blue(n) -> n\n'),
 ("a constant pattern", 'LIM = 5\nfn f(n Int) Int\n  when n\n    LIM -> 1\n    else 2\n'),
]
fails = []
for name, src, word in WARN:
    rc, o = check(src)
    ok = rc == 0 and "warning" in o and word in o
    print(("ok    " if ok else "FAIL  ") + "warns: " + name + ("" if ok else f"  {o.strip()[:160]!r}"))
    if not ok: fails.append(name)
for name, src in QUIET:
    rc, o = check(src)
    ok = rc == 0 and "warning" not in o
    print(("ok    " if ok else "FAIL  ") + "quiet: " + name + ("" if ok else f"  {o.strip()[:160]!r}"))
    if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
