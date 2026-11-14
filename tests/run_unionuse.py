"""A value of a `type union` is one of its members: using it as one is an error until `is` or `when` says which.  Run: python3 tests/run_unionuse.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
U = 'type union IT = Int | String\n'
U3 = 'type union IBT = Int | Bool | String\n'
P = U + 'tuple P\n  v IT\n'
OK = [
 ("is narrows the then-branch", U + 'fn g(v IT) Int\n  if v is Int\n    v + 1\n  else\n    0\nprintln(g(4))\nprintln(g("a"))\n', "5\n0\n"),
 ("two members: the else is the other one", U + 'fn g(v IT) Int\n  if v is Int\n    v\n  else\n    len(v)\nprintln(g(4))\nprintln(g("abc"))\n', "4\n3\n"),
 ("an elif chain", U3 + 'fn g(v IBT) Int\n  if v is Int\n    v\n  elif v is Bool\n    1\n  else\n    len(v)\nprintln(g(4))\nprintln(g(true))\nprintln(g("ab"))\n', "4\n1\n2\n"),
 ("and narrows its right side", U + 'fn g(v IT) Bool\n  v is Int and v > 0\nprintln(g(3))\nprintln(g(-3))\nprintln(g("a"))\n', "true\nfalse\nfalse\n"),
 ("a field path", P + 'fn g(p P) Int\n  if p.v is Int\n    p.v + 1\n  else\n    0\nprintln(g(P(v: 1)))\nprintln(g(P(v: "a")))\n', "2\n0\n"),
 ("when arms", U + 'fn g(v IT) Int\n  when v\n    Int -> v + 1\n    String -> len(v)\nprintln(g(1))\nprintln(g("ab"))\n', "2\n2\n"),
 ("a union passes to a union parameter and back", U + 'fn h(v IT) IT = v\nfn g(v IT) IT\n  h(v)\nprintln(g(1))\n', "1\n"),
 ("show and interpolation take any value", U + 'fn g(v IT) String\n  "got $v"\nprintln(g(1))\nprintln(g("a"))\n', "got 1\ngot a\n"),
 ("equality with a member", U + 'fn g(v IT) Bool\n  v == 1\nprintln(g(1))\nprintln(g(2))\n', "true\nfalse\n"),
 ("a bound alias stays a union", U + 'fn g(v IT) Int\n  w = v\n  if w is Int\n    w\n  else\n    0\nprintln(g(5))\n', "5\n"),
]
ERR = [
 ("arithmetic on a union", U + 'fn g(v IT) Int\n  v + 1\n', "test it first"),
 ("a member function on a union", U + 'fn g(v IT) Int\n  len(v)\n', "can't take"),
 ("the wrong member in the then-branch", U + 'fn g(v IT) Int\n  if v is Int\n    len(v)\n  else\n    0\n', "can't take"),
 ("the wrong member in the else", U + 'fn g(v IT) Int\n  if v is Int\n    0\n  else\n    v + 1\n', "cannot apply"),
 ("narrowing ends with the branch", U + 'fn g(v IT) Int\n  if v is Int\n    println("int")\n  v + 1\n', "test it first"),
 ("a field that is a union", P + 'fn g(p P) Int\n  p.v + 1\n', "test it first"),
 ("a typed binding", U + 'fn g(v IT) Int\n  w Int = v\n  w\n', "found `Int | String`"),
 ("a concrete parameter", U + 'fn h(n Int) Int = n\nfn g(v IT) Int\n  h(v)\n', "found `Int | String`"),
 ("negating a union", U + 'fn g(v IT) Int\n  -v\n', "test which member"),
 ("the path is not narrowed once tested elsewhere", P + 'fn g(p P, q P) Int\n  if p.v is Int\n    q.v + 1\n  else\n    0\n', "test it first"),
]
fails = []
for name, src, want in OK:
    rc, out = run(src)
    good = rc == 0 and out == want
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
    if not good:
        fails.append(name)
for name, src, word in ERR:
    rc, out = run(src, "check")
    good = rc != 0 and word in out
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
    if not good:
        fails.append(name)
sys.exit(1 if fails else 0)
