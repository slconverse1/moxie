"""Compile-time proof of results (`where` after the result type) and of tuple fields (`invariant`, `where` after a field).
Run: python3 tests/run_proveexit.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACC = "tuple Account deriving show\n  balance Int where balance >= 0\n"
CASES = [
 # (name, source, flags, want rc, text in output, text that must not be in output)
 ("an if proves the result", "fn abs(n Int) Int where result >= 0\n  if n < 0\n    0 - n\n  else\n    n\nprintln(abs(-3))\n", ["check"], 0, "main.mxi: ok", "warning"),
 ("a result where proves the result from the parameter", "fn inc(x Int) Int where result > x\n  x + 1\nprintln(inc(1))\n", ["check"], 0, "main.mxi: ok", "warning"),
 ("a return and the last line both prove", "fn big(n Int) Int where result >= 10\n  if n > 5\n    return n + 100\n  10\nprintln(big(1))\n", ["check"], 0, "main.mxi: ok", "warning"),
 ("a where on the parameter helps", "fn inc(n Int where n >= 0) Int where result > 0 = n + 1\nprintln(inc(1))\n", ["check"], 0, "main.mxi: ok", "warning"),
 ("a result that can never hold is an error", "fn bad(n Int where n > 0) Int where result < 0 = n\n", ["check"], 2, "promises `result < 0`", None),
 ("an unknown result says nothing", "fn id(n Int) Int where result >= 0 = n\nprintln(id(1))\n", ["check"], 0, "main.mxi: ok", "warning"),
 ("--prove makes an unknown result an error", "fn id(n Int) Int where result >= 0 = n\n", ["--prove", "check"], 2, "can't prove `result >= 0` for the result of `id`", None),
 ("a field is proved from a where on the argument", ACC + "fn mk(n Int where n >= 0) Account = Account(balance: n)\nprintln(mk(2))\n", ["check"], 0, "main.mxi: ok", "warning"),
 ("a field is proved by a test", ACC + "fn mk(n Int) Account\n  if n >= 0\n    Account(balance: n)\n  else\n    Account(balance: 0)\nprintln(mk(2))\n", ["check"], 0, "main.mxi: ok", "warning"),
 ("a field that can never hold is an error", ACC + "x = Account(balance: -1)\n", ["check"], 2, "needs `balance >= 0`", None),
 ("an unknown field says nothing", ACC + "fn mk(n Int) Account = Account(balance: n)\nprintln(mk(2))\n", ["check"], 0, "main.mxi: ok", "warning"),
 ("--prove makes an unknown field an error", ACC + "fn mk(n Int) Account = Account(balance: n)\n", ["--prove", "check"], 2, "can't prove `balance >= 0` for `Account`", None),
 ("a header field is proved", "tuple Box(w Int where w > 0, h Int) deriving show\nprintln(Box(2, 3))\n", ["check"], 0, "main.mxi: ok", "warning"),
 ("a rebuild with a spread is left to the run-time check", ACC + "a = Account(balance: 1)\nprintln(Account(...a, balance: 2))\n", ["check"], 0, "main.mxi: ok", "warning"),
]
fails = []
for name, src, flags, rc, want, nowant in CASES:
    for gc in (False, True):
        d = tempfile.mkdtemp()
        open(os.path.join(d, "main.mxi"), "w").write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + flags + [os.path.join(d, "main.mxi")]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        o = r.stdout + r.stderr
        ok = want in o and (r.returncode == 0) == (rc == 0) and (nowant is None or nowant not in o)
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o[:300]!r}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
