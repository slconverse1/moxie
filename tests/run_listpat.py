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
case('a name binds the whole value', U + 'fn f(d: Data) Int:\n  when d:\n    List[Int] -> d(0) + 1\n    xs@List[String] -> len(xs(0))\n    Int -> d\nprintln(f(List(5)))\nprintln(f(List("abc")))' + '\n', 0, '6\n3')
case('is tests a List member', U + 'fn f(d: Data) Bool:\n  d is List[String]\nprintln(f(List("a")))\nprintln(f(List(1)))\nprintln(f(3))' + '\n', 0, 'true\nfalse\nfalse')
case('an arm narrows the type', U + 'fn f(d: Data) Int:\n  when d:\n    List[Int] -> d(0) + 1\n    List[String] -> d(0) + 1\n    Int -> d\nprintln(f(List(5)))' + '\n', 2, 'cannot apply `+` to `String` and `Int`')

case("an empty List is told apart by its static type", U + 'fn f(d: Data) String:\n  when d:\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nxs: List[String] = List()\nprintln(f(xs))\nprintln(f(List[String]()))\nprintln(f(List[Int]()))\nd: Data = List[String]()\nprintln(f(d))\n', 0, "strings\nstrings\nints\nstrings")
case("a member left out of a when is a compile error", U + 'fn f(d: Data) String:\n  when d:\n    List[Int] -> "ints"\n    Int -> "one"\nprintln(f(3))\n', 2, "`when` does not cover `List[String]`")
case("a plain union member left out is a compile error", 'type union V = Int | String\nfn f(v: V) String:\n  when v:\n    Int -> "n"\nprintln(f(1))\n', 2, "`when` does not cover `String`")
case("a _ arm covers the rest", U + 'fn f(d: Data) String:\n  when d:\n    List[Int] -> "ints"\n    _ -> "other"\nprintln(f(3))\n', 0, "other")
case("every member named is exhaustive", 'type union V = Int | String\nfn f(v: V) String:\n  when v:\n    Int -> "n"\n    String -> "s"\nprintln(f(1))\n', 0, "n")

case("an empty List keeps its member through returns and collections", U + 'fn f(d: Data) String:\n  when d:\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nfn make() Data:\n  List[String]()\nfn make2(flag: Bool) Data:\n  if flag:\n    List[String]()\n  else:\n    List[Int]()\nfn make3() Data:\n  return List[String]()\nprintln(f(make()))\nprintln(f(make2(true)))\nprintln(f(make2(false)))\nprintln(f(make3()))\nitems = List[Data](List[String](), List[Int](), 3)\nfor x in items:\n  println(f(x))\nmore: List[Data] = List(List[String](), List[Int]())\nfor x in more:\n  println(f(x))\n', 0, "strings\nstrings\nints\nstrings\nstrings\nints\none\nstrings\nints")
case("a local of a union type must be covered too", U + 'd: Data = List[String]()\nwhen d:\n  List[Int] -> println("ints")\n  Int -> println("one")\n', 2, "`when` does not cover `List[String]`")
case("a local of a union type is narrowed", U + 'd: Data = List(1, 2)\nwhen d:\n  List[Int] -> println(d(0) + 1)\n  List[String] -> println(len(d(0)))\n  Int -> println(d)\n', 0, "2")

case("an empty List keeps its member through a lambda", U + 'fn f(d: Data) String:\n  when d:\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nfn apply(g: (Int) -> Data, n: Int) Data:\n  g(n)\nprintln(f(apply((n): List[String](), 1)))\nprintln(f(apply((n): List[Int](), 1)))\nh: (Int) -> Data = (n):\n  if n > 0:\n    List[String]()\n  else:\n    List[Int]()\nprintln(f(h(1)))\nprintln(f(h(0)))\ng: (Int) -> Data = (n): List[String]()\nprintln(f(g(1)))\n', 0, "strings\nints\nstrings\nints\nstrings")

print()
print('FAILURES: ' + ', '.join(fails) if fails else 'all List pattern tests passed')
sys.exit(1 if fails else 0)
