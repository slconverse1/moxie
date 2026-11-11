"""A `type union` with `List[T]` members taken apart by `when` arms and `is`.  Run: python3 tests/run_listpat.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []

def run(src, *args):
    d = tempfile.mkdtemp(prefix="mxfmt")
    p = os.path.join(d, "t.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", *("moxie",) , *args, p], cwd=ROOT, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr

def case(name, src, rc_want, *wants, args=()):
    rc, out = run(src, *args)
    ok = rc == rc_want and all(w in out for w in wants)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
    if not ok:
        fails.append(name)

U = 'type union Data = List[Int] | List[String] | Int\n'

case('when takes apart List members', U + 'fn f(d: Data) String:\n  when d:\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nprintln(f(List(1, 2)))\nprintln(f(List("a")))\nprintln(f(3))' + '\n', 0, 'ints\nstrings\none')
case('an empty List matches the first List arm', U + 'fn f(d: Data) String:\n  when d:\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nprintln(f(List[String]()))' + '\n', 0, 'ints')
case('a name binds the whole value', U + 'fn f(d: Data) Int:\n  when d:\n    List[Int] -> d(0) + 1\n    xs@List[String] -> len(xs(0))\n    Int -> d\nprintln(f(List(5)))\nprintln(f(List("abc")))' + '\n', 0, '6\n3')
case('is tests a List member', U + 'fn f(d: Data) Bool:\n  d is List[String]\nprintln(f(List("a")))\nprintln(f(List(1)))\nprintln(f(3))' + '\n', 0, 'true\nfalse\nfalse')
case('an arm narrows the type', U + 'fn f(d: Data) Int:\n  when d:\n    List[Int] -> d(0) + 1\n    List[String] -> d(0) + 1\n    Int -> d\nprintln(f(List(5)))' + '\n', 2, 'cannot apply `+` to `String` and `Int`')

print()
print('FAILURES: ' + ', '.join(fails) if fails else 'all List pattern tests passed')
sys.exit(1 if fails else 0)
