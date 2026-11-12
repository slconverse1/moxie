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

case('when takes apart List members', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nprintln(f(List(1, 2)))\nprintln(f(List("a")))\nprintln(f(3))' + '\n', 0, 'ints\nstrings\none')
case('a name binds the whole value', U + 'fn f(d Data) Int\n  when d\n    List[Int] -> d(0) + 1\n    xs@List[String] -> len(xs(0))\n    Int -> d\nprintln(f(List(5)))\nprintln(f(List("abc")))' + '\n', 0, '6\n3')
case('is tests a List member', U + 'fn f(d Data) Bool\n  d is List[String]\nprintln(f(List("a")))\nprintln(f(List(1)))\nprintln(f(3))' + '\n', 0, 'true\nfalse\nfalse')
case('an arm narrows the type', U + 'fn f(d Data) Int\n  when d\n    List[Int] -> d(0) + 1\n    List[String] -> d(0) + 1\n    Int -> d\nprintln(f(List(5)))' + '\n', 2, 'cannot apply `+` to `String` and `Int`')

case("an empty List is told apart by its static type", U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nxs: List[String] = List()\nprintln(f(xs))\nprintln(f(List[String]()))\nprintln(f(List[Int]()))\nd: Data = List[String]()\nprintln(f(d))\n', 0, "strings\nstrings\nints\nstrings")
case("a member left out of a when is a compile error", U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    Int -> "one"\nprintln(f(3))\n', 2, "`when` does not cover `List[String]`")
case("a plain union member left out is a compile error", 'type union V = Int | String\nfn f(v V) String\n  when v\n    Int -> "n"\nprintln(f(1))\n', 2, "`when` does not cover `String`")
case("a _ arm covers the rest", U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    _ -> "other"\nprintln(f(3))\n', 0, "other")
case("every member named is exhaustive", 'type union V = Int | String\nfn f(v V) String\n  when v\n    Int -> "n"\n    String -> "s"\nprintln(f(1))\n', 0, "n")

case("an empty List keeps its member through returns and collections", U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nfn make() Data\n  List[String]()\nfn make2(flag Bool) Data\n  if flag\n    List[String]()\n  else\n    List[Int]()\nfn make3() Data\n  return List[String]()\nprintln(f(make()))\nprintln(f(make2(true)))\nprintln(f(make2(false)))\nprintln(f(make3()))\nitems = List[Data](List[String](), List[Int](), 3)\nfor x in items\n  println(f(x))\nmore: List[Data] = List(List[String](), List[Int]())\nfor x in more\n  println(f(x))\n', 0, "strings\nstrings\nints\nstrings\nstrings\nints\none\nstrings\nints")
case("a local of a union type must be covered too", U + 'd: Data = List[String]()\nwhen d\n  List[Int] -> println("ints")\n  Int -> println("one")\n', 2, "`when` does not cover `List[String]`")
case("a local of a union type is narrowed", U + 'd: Data = List(1, 2)\nwhen d\n  List[Int] -> println(d(0) + 1)\n  List[String] -> println(len(d(0)))\n  Int -> println(d)\n', 0, "2")

case("an empty List keeps its member through a lambda", U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nfn apply(g (Int) -> Data, n Int) Data\n  g(n)\nprintln(f(apply((n) -> List[String](), 1)))\nprintln(f(apply((n) -> List[Int](), 1)))\nh: (Int) -> Data = (n) ->\n  if n > 0\n    List[String]()\n  else\n    List[Int]()\nprintln(f(h(1)))\nprintln(f(h(0)))\ng: (Int) -> Data = (n) -> List[String]()\nprintln(f(g(1)))\n', 0, "strings\nints\nstrings\nints\nstrings")

case("a bare List arm against two List members is ambiguous", U + 'fn f(d Data) String\n  when d\n    List -> "a list"\n    Int -> "one"\nprintln(f(List(1)))\n', 2, "`List` could be `List[Int]` or `List[String]` here: write the full type")
case("a bare List arm names the only List member", 'type union D = List[Int] | Int\nfn f(d D) String\n  when d\n    List -> "a list"\n    Int -> "one"\nprintln(f(List(1)))\nprintln(f(List[Int]()))\nprintln(f(3))\n', 0, "a list\na list\none")
case("a bare is List against two List members is ambiguous", U + 'fn f(d Data) Bool\n  d is List\nprintln(f(List(1)))\n', 2, "`List` could be")

case('an empty List in a tuple field keeps its member', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\ntuple B\n  v Data\nb = B(v: List[String]())\nc = B(List[Int]())\nprintln(f(b.v))\nprintln(f(c.v))\n', 0, 'strings\nints')
case('an empty List in an enum case keeps its member', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nenum E\n  Box(Data)\nb = E.Box(List[String]())\nwhen b\n  E.Box(v) -> println(f(v))\n', 0, 'strings')
case('an empty List sent on a channel keeps its member', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nrx, tx = Chan[Data][1]()\n\\write(tx, List[String]())\nprintln(f(read(rx)?))\n', 0, 'strings')
case('an empty List added to a collection later keeps its member', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nitems: List[Data] = List(1)\nitems = items + List(List[String]())\nfor x in items\n  println(f(x))\n', 0, 'one\nstrings')
case('an empty List in a Dict literal keeps its member', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nd: Dict[String, Data] = Dict("a" -> List[String](), "b" -> List[Int]())\nprintln(f(d("a")?))\nprintln(f(d("b")?))\n', 0, 'strings\nints')
case('a lambda with an inferred type makes a tagged list', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\ng = () -> List[String]()\nprintln(f(g()))\nh = (n Int) -> List[Int]()\nprintln(f(h(1)))\n', 0, 'strings\nints')
case('a named empty List keeps its member in a constructor', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nys: List[String] = List()\nitems = List[Data](ys, 3)\nprintln(f(items(0)))\nmore: List[Data] = List(ys)\nprintln(f(more(0)))\n', 0, 'strings\nstrings')
case('an empty List passed through a typed parameter or result', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\nfn g(xs List[String]) String\n  f(xs)\nfn mk() List[String]\n  List()\nprintln(g(List()))\nprintln(f(mk()))\n', 0, 'strings\nstrings')

case('an empty List from a stream step keeps its member in a field', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\ntuple B\n  v Data\nys = List("a") |> to_stream() |> filter((s) -> s == "b") |> collect()\nb = B(v: ys)\nprintln(f(b.v))\n', 0, 'strings')
case('an empty List from a stream step is tagged where it is made', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\ntuple B\n  v Data\nxss = List(1) |> to_stream() |> map((n) -> List[String]()) |> collect()\nfor xs in xss\n  println(f(B(v: xs).v))\n', 0, 'strings')
case("a typed parameter's empty List keeps its member into a field", U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\ntuple B\n  v Data\nfn g(xs List[String]) B\n  B(v: xs)\nprintln(f(g(List()).v))\n', 0, 'strings')
case("a typed field's empty List keeps its member", U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\ntuple B\n  v Data\ntuple C\n  w List[String]\nc = C(w: List())\nprintln(f(B(v: c.w).v))\n', 0, 'strings')
case('empty Lists nested in a typed List keep their members', U + 'fn f(d Data) String\n  when d\n    List[Int] -> "ints"\n    List[String] -> "strings"\n    Int -> "one"\ntuple B\n  v Data\nxss: List[List[String]] = List(List(), List())\nfor xs in xss\n  println(f(B(v: xs).v))\n', 0, 'strings\nstrings')

case('a when on a call that gives a union must cover it', 'type union V = Int | String\ntuple W\n  v V\nfn mk() V\n  3\nwhen mk()\n  Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a when on a call that gives a union, covered', 'type union V = Int | String\ntuple W\n  v V\nfn mk() V\n  3\nwhen mk()\n  Int -> println("n")\n  String -> println("s")\n', 0, 'n')
case('a when on a field of a union type must cover it', 'type union V = Int | String\ntuple W\n  v V\nfn mk() V\n  3\nw = W(v: 1)\nwhen w.v\n  Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a when on a list element of a union type must cover it', 'type union V = Int | String\ntuple W\n  v V\nfn mk() V\n  3\nvs: List[V] = List(1, "a")\nwhen vs(0)\n  String -> println("s")\n', 2, '`when` does not cover `Int`')
case('a when on a loop variable over a union list must cover it', 'type union V = Int | String\ntuple W\n  v V\nfn mk() V\n  3\nvs: List[V] = List(1, "a")\nfor x in vs\n  when x\n    Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a binding arm covers the rest of a union call', 'type union V = Int | String\ntuple W\n  v V\nfn mk() V\n  3\nwhen mk()\n  n@Int -> println(n)\n  other -> println("o")\n', 0, '3')

case('the branches of an if may be different members of the result union', 'type union V = Int | String\nfn g(n Int) V\n  if n > 0 then n else "neg"\nprintln(g(1))\nprintln(g(0))\n', 0, '1\nneg')
case('the arms of a when may be different members of the result union', 'type union V = Int | String\nfn g(n Int) V\n  when n\n    0 -> "zero"\n    _ -> n\nprintln(g(0))\n', 0, 'zero')
case('an annotated union binding takes branches of different members', 'type union V = Int | String\nx: V = if true then 1 else "a"\nprintln(x)\n', 0, '1')
case('branches that are not members of the union are still an error', 'type union W = Int | Bool\nfn g(n Int) W\n  if n > 0 then n else "neg"\nprintln(g(1))\n', 2, 'have different types')
case('branches of different types where no union is expected are still an error', 'fn g(n Int) Int\n  if n > 0 then n else "neg"\nprintln(g(1))\n', 2, 'have different types')

case('a when on a method result must cover the union', 'type union V = Int | String\ntuple W\n  v V\nimpl W\n  fn get(self) V\n    self.v\n  static fn make() V\n    3\nw = W(v: 1)\nwhen w.get()\n  Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a when on a static call result must cover the union', 'type union V = Int | String\ntuple W\n  v V\nimpl W\n  fn get(self) V\n    self.v\n  static fn make() V\n    3\nwhen W.make()\n  Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a when on a Dict value in a for must cover the union', 'type union V = Int | String\ntuple W\n  v V\nimpl W\n  fn get(self) V\n    self.v\n  static fn make() V\n    3\nd: Dict[String, V] = Dict("a" -> 1, "b" -> "x")\nfor k, v in d\n  when v\n    Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a when on a Dict value in a for, covered', 'type union V = Int | String\ntuple W\n  v V\nimpl W\n  fn get(self) V\n    self.v\n  static fn make() V\n    3\nd: Dict[String, V] = Dict("a" -> 1, "b" -> "x")\nfor k, v in d\n  when v\n    Int -> println("n")\n    String -> println("s")\n', 0, 'n\ns')
case('a when on a local bound to a union call must cover it', 'type union V = Int | String\ntuple W\n  v V\nimpl W\n  fn get(self) V\n    self.v\n  static fn make() V\n    3\nfn mk() V\n  3\nx = mk()\nwhen x\n  Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a when on a generic result of a union list must cover it', 'type union V = Int | String\ntuple W\n  v V\nimpl W\n  fn get(self) V\n    self.v\n  static fn make() V\n    3\nfn first[T](xs List[T]) T\n  xs(0)\nvs: List[V] = List(1)\nwhen first(vs)\n  Int -> println("n")\n', 2, '`when` does not cover `String`')

case('a when on a ? result of a union must cover it', 'type union V = Int | String\nfn mk() Result[V, Error]\n  Ok(1)\nfn mo() Option[V]\n  Some(1)\nenum Box\n  Full(v V)\n  Empty\ntuple P\n  a V\nfn f() Result[Int, Error]\n  when mk()?\n    Int -> Ok(1)\nprintln(f())\n', 2, '`when` does not cover `String`')
case('a name bound by Ok knows its union', 'type union V = Int | String\nfn mk() Result[V, Error]\n  Ok(1)\nfn mo() Option[V]\n  Some(1)\nenum Box\n  Full(v V)\n  Empty\ntuple P\n  a V\nwhen mk()\n  Ok(v) ->\n    when v\n      Int -> println("n")\n  Err(e) -> println("e")\n', 2, '`when` does not cover `String`')
case('a name bound by Some knows its union', 'type union V = Int | String\nfn mk() Result[V, Error]\n  Ok(1)\nfn mo() Option[V]\n  Some(1)\nenum Box\n  Full(v V)\n  Empty\ntuple P\n  a V\nwhen mo()\n  Some(v) ->\n    when v\n      Int -> println("n")\n  None -> println("none")\n', 2, '`when` does not cover `String`')
case('a name bound by an enum case knows its union', 'type union V = Int | String\nfn mk() Result[V, Error]\n  Ok(1)\nfn mo() Option[V]\n  Some(1)\nenum Box\n  Full(v V)\n  Empty\ntuple P\n  a V\nwhen Box.Full(1)\n  Full(v) ->\n    when v\n      Int -> println("n")\n  Empty -> println("e")\n', 2, '`when` does not cover `String`')
case('a name bound by a tuple pattern knows its union', 'type union V = Int | String\nfn mk() Result[V, Error]\n  Ok(1)\nfn mo() Option[V]\n  Some(1)\nenum Box\n  Full(v V)\n  Empty\ntuple P\n  a V\np = P(a: 1)\nwhen p\n  P(a) ->\n    when a\n      Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a name bound by a destructuring assignment knows its union', 'type union V = Int | String\nfn mk() Result[V, Error]\n  Ok(1)\nfn mo() Option[V]\n  Some(1)\nenum Box\n  Full(v V)\n  Empty\ntuple P\n  a V\np = P(a: 1)\nP(a) = p\nwhen a\n  Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a name bound by an is test knows its union', 'type union V = Int | String\nfn mk() Result[V, Error]\n  Ok(1)\nfn mo() Option[V]\n  Some(1)\nenum Box\n  Full(v V)\n  Empty\ntuple P\n  a V\nfn f(b Box) Int\n  if b is Full(v)\n    when v\n      Int -> 1\n  else\n    0\nprintln(f(Box.Empty))\n', 2, '`when` does not cover `String`')
case('a payload name covered in full is accepted', 'type union V = Int | String\nfn mk() Result[V, Error]\n  Ok(1)\nfn mo() Option[V]\n  Some(1)\nenum Box\n  Full(v V)\n  Empty\ntuple P\n  a V\nwhen mk()\n  Ok(v) ->\n    when v\n      Int -> println("n")\n      String -> println("s")\n  Err(e) -> println("e")\n', 0, 'n')

case('a when on a typed lambda parameter must cover the union', 'type union V = Int | String\nenum Box[T]\n  Full(v T)\n  Empty\nenum Level(code V)\n  Low(1)\n  High("h")\nf = (v V) ->\n  when v\n    Int -> 1\nprintln(f(2))\n', 2, '`when` does not cover `String`')
case('a typed lambda parameter covered in full is accepted', 'type union V = Int | String\nenum Box[T]\n  Full(v T)\n  Empty\nenum Level(code V)\n  Low(1)\n  High("h")\nf = (v V) ->\n  when v\n    Int -> 1\n    String -> 2\nprintln(f(2))\n', 0, '1')
case('a name bound by a generic enum knows its union', 'type union V = Int | String\nenum Box[T]\n  Full(v T)\n  Empty\nenum Level(code V)\n  Low(1)\n  High("h")\nb: Box[V] = Box.Full(1)\nwhen b\n  Full(v) ->\n    when v\n      Int -> println("n")\n  Empty -> println("e")\n', 2, '`when` does not cover `String`')
case('a generic enum payload covered in full is accepted', 'type union V = Int | String\nenum Box[T]\n  Full(v T)\n  Empty\nenum Level(code V)\n  Low(1)\n  High("h")\nb: Box[V] = Box.Full(1)\nwhen b\n  Full(v) ->\n    when v\n      Int -> println("n")\n      String -> println("s")\n  Empty -> println("e")\n', 0, 'n')
case('a name bound by a header enum case knows its union', 'type union V = Int | String\nenum Box[T]\n  Full(v T)\n  Empty\nenum Level(code V)\n  Low(1)\n  High("h")\nwhen Level.Low\n  Low(c) ->\n    when c\n      Int -> println("n")\n  High(c) -> println("h")\n', 2, '`when` does not cover `String`')

case("a name bound to a list literal's element is checked", 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nxs = List(mk(1), mk(2))\nv = xs(0)\nwhen v\n  Int -> println("n")\n', 2, '`when` does not cover `String`')
case("a name bound to a list literal's element covered in full is accepted", 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nxs = List(mk(1), mk(2))\nv = xs(0)\nwhen v\n  Int -> println("n")\n  String -> println("s")\n', 0, '')
case('an `if` whose branches are all a union is checked', 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nv = if true then mk(1) else mk(2)\nwhen v\n  Int -> println("n")\n', 2, '`when` does not cover `String`')
case('an `if` whose branches are all a union covered in full is accepted', 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nv = if true then mk(1) else mk(2)\nwhen v\n  Int -> println("n")\n  String -> println("s")\n', 0, '')
case('a loop over an unannotated list literal is checked', 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nxs = List(mk(1))\nfor v in xs\n  when v\n    Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a loop over an unannotated list literal, covered, is accepted', 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nxs = List(mk(1))\nfor v in xs\n  when v\n    Int -> println("n")\n    String -> println("s")\n', 0, 'n')
case('the result of `map` with a union-returning lambda is checked', 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nxs = List(1) |> map((n) -> mk(n))\nv = xs(0)\nwhen v\n  Int -> println("n")\n', 2, '`when` does not cover `String`')
case('the result of `map` with a union-returning lambda covered in full is accepted', 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nxs = List(1) |> map((n) -> mk(n))\nv = xs(0)\nwhen v\n  Int -> println("n")\n  String -> println("s")\n', 0, '')
case("a Dict literal's values are checked in a for", 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nd = Dict("a" -> mk(1))\nfor k, v in d\n  when v\n    Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a call of a lambda bound to a name is checked', 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nf = (n Int) -> mk(n)\nv = f(1)\nwhen v\n  Int -> println("n")\n', 2, '`when` does not cover `String`')
case('a call of a lambda bound to a name covered in full is accepted', 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nf = (n Int) -> mk(n)\nv = f(1)\nwhen v\n  Int -> println("n")\n  String -> println("s")\n', 0, '')
case('branches that are not all the same union are not guessed at', 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nv = if true then mk(1) else 5\nwhen v\n  Int -> println("n")\n', 0, 'n')
case('a lambda that returns its own parameter is not mistaken for an outer name', 'type union V = Int | String\nfn mk(n Int) V\n  if n > 0 then n else "s"\nv = mk(1)\nf = (v) -> v\nw = f(2)\nwhen w\n  Int -> println("n")\n', 0, 'n')

print()
print('FAILURES: ' + ', '.join(fails) if fails else 'all List pattern tests passed')
sys.exit(1 if fails else 0)
