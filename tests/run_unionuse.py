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
 ("early return narrows the rest", U + 'fn g(v IT) Int\n  if not (v is Int) then return 0\n  v + 1\nprintln(g(4))\nprintln(g("a"))\n', "5\n0\n"),
 ("early return from a block", U + 'fn g(v IT) Int\n  if v is String\n    return len(v)\n  v + 1\nprintln(g(4))\nprintln(g("abc"))\n', "5\n3\n"),
 ("a guard that returns", U + 'fn g(v IT) Int\n  return 0 if v is String\n  v + 1\nprintln(g(4))\nprintln(g("a"))\n', "5\n0\n"),
 ("a guard with else", U + 'fn g(v IT) Int\n  println("int") if v is Int else 0\n  v + 1\nprintln(g(4))\nprintln(g("a"))\n', "int\n5\n0\n"),
 ("continue narrows the rest of the loop body", U + 'fn g(xs List[IT]) Unit\n  for x in xs\n    if x is String then continue\n    println(x + 1)\ng(List(1, 5))\n', "2\n6\n"),
 ("early exit on a field path", P + 'fn g(p P) Int\n  if p.v is String then return 0\n  p.v + 1\nprintln(g(P(v: 1)))\nprintln(g(P(v: "a")))\n', "2\n0\n"),
 ("not swaps the branches", U + 'fn g(v IT) Int\n  if not (v is Int)\n    0\n  else\n    v + 1\nprintln(g(1))\nprintln(g("a"))\n', "2\n0\n"),
 ("or narrows its right side", U + 'fn g(v IT) Bool\n  v is String or v > 0\nprintln(g(1))\nprintln(g(-1))\nprintln(g("a"))\n', "true\nfalse\ntrue\n"),
 ("or keeps a union of what is left", U3 + 'fn h(v IBT) Int = 7\nfn g(v IBT) Int\n  if v is Int or v is String\n    h(v)\n  else\n    0\nprintln(g(1))\nprintln(g(true))\n', "7\n0\n"),
 ("a union of what is left narrows again", U3 + 'fn g(v IBT) Int\n  if v is Bool then return 0\n  if v is Int\n    v + 1\n  else\n    len(v)\nprintln(g(1))\nprintln(g("ab"))\nprintln(g(true))\n', "2\n2\n0\n"),
 ("a loop variable over a list of a union", U + 'fn g(xs List[IT]) Unit\n  for x in xs\n    if x is Int\n      println(x + 1)\n    else\n      println(len(x))\ng(List(1, "abc"))\n', "2\n3\n"),
 ("a Dict value in a loop", U + 'fn g(d Dict[String, IT]) Unit\n  for k, v in d\n    if v is Int then println(v + 1)\ng(Dict("a" -> 1))\n', "2\n"),
 ("an element by literal index", U + 'fn g(xs List[IT]) Int\n  if xs(0) is Int\n    xs(0) + 1\n  else\n    0\nprintln(g(List(4)))\nprintln(g(List("a")))\n', "5\n0\n"),
 ("an element by a name", U + 'fn g(xs List[IT], i Int) Int\n  if xs(i) is String then return len(xs(i))\n  xs(i) + 1\nprintln(g(List(4, "abc"), 0))\nprintln(g(List(4, "abc"), 1))\n', "5\n3\n"),
 ("early exit from an elif chain", U3 + 'fn g(v IBT) Int\n  if v is Bool\n    return 0\n  elif v is String\n    return len(v)\n  v + 1\nprintln(g(1))\nprintln(g(true))\nprintln(g("ab"))\n', "2\n0\n2\n"),
 ("an elif chain where the arms that stay agree", U3 + 'fn h(v IBT) Int = 9\nfn g(v IBT) Int\n  if v is Bool\n    println("b")\n  elif v is Int\n    println("i")\n  else\n    return 0\n  h(v)\nprintln(g(1))\nprintln(g("a"))\n', "i\n9\n0\n"),
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
 ("a branch that does not leave narrows nothing", U + 'fn g(v IT) Int\n  if v is String\n    println("s")\n  v + 1\n', "test it first"),
 ("not names the wrong member", U + 'fn g(v IT) Int\n  if not (v is Int)\n    v + 1\n  else\n    0\n', "cannot apply"),
 ("what is left of three is still a union", U3 + 'fn g(v IBT) Int\n  if v is Bool\n    0\n  else\n    v + 1\n', "test it first"),
 ("or does not narrow when only one part holds", U3 + 'fn g(v IBT) Int\n  if v is Int or v is Bool\n    v + 1\n  else\n    0\n', "test it first"),
 ("a loop variable over a list of a union", U + 'fn g(xs List[IT]) Unit\n  for x in xs\n    println(x + 1)\n', "test it first"),
 ("an element of a list of a union", U + 'fn g(xs List[IT]) Int\n  xs(0) + 1\n', "test it first"),
 ("a test of one element says nothing about another", U + 'fn g(xs List[IT]) Int\n  if xs(0) is Int\n    xs(1) + 1\n  else\n    0\n', "test it first"),
 ("a test of an element by one name does not cover another", U + 'fn g(xs List[IT], i Int, j Int) Int\n  if xs(i) is Int\n    xs(j) + 1\n  else\n    0\n', "test it first"),
 ("an elif arm that stays and does not narrow", U3 + 'fn g(v IBT) Int\n  if v is Bool\n    return 0\n  elif v is String\n    println("s")\n  v + 1\n', "test it first"),
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
