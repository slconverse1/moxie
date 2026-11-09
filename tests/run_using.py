"""Contextual parameters (`using`): found by type from the call's scope.  Run: python3 tests/run_using.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CTX = '''tuple Context:
  user: String
fn send(url: String, using ctx: Context) Unit:
  println("${url} ${ctx.user}")
'''

# (name, source, how, text): how is "run" (exit 0 and text in output) or "fail" (nonzero exit and text in output)
CASES = [
 ("a top-level using is found by type, whatever the names",
  CTX + 'using c = Context(user: "ann")\nsend("u", using)\n', "run", "u ann"),
 ("a using declared inside a function body is found at the call",
  CTX + 'fn go() Unit:\n  using c = Context(user: "ann")\n  send("u", using)\ngo()\n', "run", "u ann"),
 ("the innermost scope wins",
  CTX + 'using c = Context(user: "outer")\nfn go() Unit:\n  using d = Context(user: "inner")\n  send("u", using)\ngo()\nsend("v", using)\n', "run", "u inner\nv outer"),
 ("two values of the type in one scope are ambiguous",
  CTX + 'using a = Context(user: "ann")\nusing b = Context(user: "bob")\nsend("u", using)\n', "fail", "ambiguous"),
 ("two in one function scope are ambiguous too",
  CTX + 'fn go() Unit:\n  using a = Context(user: "ann")\n  using b = Context(user: "bob")\n  send("u", using)\ngo()\n', "fail", "ambiguous"),
 ("values of different types don't clash",
  CTX + 'tuple Other:\n  n: Int\nusing a = Context(user: "ann")\nusing b = Other(n: 1)\nsend("u", using)\n', "run", "u ann"),
 ("a using parameter is a candidate for calls in the body",
  'tuple Context:\n  user: String\nfn inner(using ctx: Context) Unit:\n  println("inner ${ctx.user}")\nfn outer(n: Int, using ctx: Context) Unit:\n  inner(using)\nfn go() Unit:\n  using c = Context(user: "zed")\n  outer(1, using)\ngo()\n', "run", "inner zed"),
 ("no value in scope is an error",
  CTX + 'send("u", using)\n', "fail", "no 'using' value"),
]

fails = []
for name, src, how, word in CASES:
    for gc in (False, True):
        if how == "nogc-fail" and gc:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        want_fail = how in ("fail", "nogc-fail")
        ok = ((r.returncode != 0) if want_fail else (r.returncode == 0)) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:300]}"))
        if not ok:
            fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
