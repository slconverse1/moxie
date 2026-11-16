"""A generic function that passes its own type parameter on (`h2[R](n)`, `build[R](x)`).  Run: python3 tests/run_targforward.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
K = "interface K\n  static fn mk(n Int) Self\ntuple A\n  v Int\nimpl K for A\n  static fn mk(n Int) A\n    A(v: n)\n"
CASES = [
 ("forwarded to another generic fn", K + "fn h2[R K](n Int) R\n  R.mk(n)\nfn h[R K](n Int) R\n  h2[R](n)\nprintln(h[A](2).v)\n", "2"),
 ("forwarded in a recursion", K + "fn g[R K](n Int) R\n  if n == 0 then R.mk(7) else g[R](n - 1)\nprintln(g[A](3).v)\n", "7"),
 ("forwarded from a when arm", K + "enum T\n  Z\n  S(t T)\nfn build[R K](t T) R\n  when t\n    Z -> R.mk(0)\n    S(u) -> build[R](u)\nprintln(build[A](T.S(T.Z)).v)\n", "0"),
]
fails = []
for name, src, want in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name], cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = (r.stdout + r.stderr).strip()
        ok = r.returncode == 0 and o == want
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
