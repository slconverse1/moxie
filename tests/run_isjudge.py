"""`is` tests that cannot vary: tuple patterns with sub-patterns, generic tuples, refutable parts.  Run: python3 tests/run_isjudge.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
H = "tuple Dog\n  name String\ntuple Cat\n  name String\ntuple Box[T]\n  v T\ntype union Pet = Dog | Cat\ntuple Fish\n  name String\n"
CASES = [
 ("a Dog pattern with a binding on a Dog", H + "fn f(d Dog) Int\n  if d is Dog(n)\n    1\n  else\n    2\n", "always a `Dog`"),
 ("a generic tuple pattern on a Box[Int]", H + "fn f(b Box[Int]) Int\n  if b is Box(x)\n    1\n  else\n    2\n", "always a `Box`"),
 ("a Cat is never a Dog even with a sub-pattern", H + 'fn f(c Cat) Int\n  if c is Dog("rex")\n    1\n  else\n    2\n', "never a `Dog`"),
 ("a union without the member, refutable part", H + 'fn f(p Pet) Int\n  if p is Fish("x")\n    1\n  else\n    2\n', "never a `Fish`"),
 ("a refutable part on the right type says nothing", H + 'fn f(d Dog) Int\n  if d is Dog("rex")\n    1\n  else\n    2\n', None),
 ("a union member is not constant", H + "fn f(p Pet) Int\n  if p is Dog(n)\n    1\n  else\n    2\n", None),
]
fails = []
for name, src, word in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check", f.name], cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = r.returncode == 0 and ((word in o) if word else "warning" not in o)
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
