"""Checker gaps: repeated type parameters in builtins, mixed-type collection literals, lambda arity."""
import sys, subprocess
BAD = [
 ("n = 7\nfn half(x: Double) Double:\n  x / 2.0\nprintln(half(n))\n", "`Int` does not convert to `Double` without loss"),
 ("n = 7\ny: Double = n\n", "`Int` does not convert to `Double` without loss"),
 ("a: Result[String, String] = Ok(\"x\")\nb: Result[String, Int] = Ok(\"y\")\nq = map_all((x, y): x, a, b)\n", "repeated type parameter"),
 ("xs = List(1, \"a\")\n", "must share one type"),
 ("xs: List[Int] = List(1, \"a\")\n", "must share one type"),
 ("a: Result[Int, String] = Ok(1)\nb: Result[Int, Int] = Ok(2)\nxs = List(a, b)\n", "must share one type"),
 ("x = List(1, 2).map((a, b): a)\n", "takes 2 parameters"),
 ("x = reduce(0, (a): a, List(1, 2))\n", "takes 1 parameter"),
 ("x = Ok(1).map((a, b): a)\n", "takes 2 parameters"),
 ("fn plain(xs: List[Int]) Int:\n  len(xs)\nprintln(plain(List(1, \"a\")))\n", "must share one type"),
 ("println(List(1, \"a\"))\n", "must share one type"),
 ("tuple Bag[T]:\n  items: List[T]\nx = map((a): a + 1, Bag(items: List(1)))\n", "`map` can't take (a function, Bag[Int])"),
 ("xs = List(1, 2, 3)\nx = any(xs, (x): x > 2)\n", "`any` can't take (List[Int], a function)"),
 ("x = map(1, 2, 3)\n", "`map` takes at most 2 arguments, but 3 given"),
 ("x = List(1) |> map((a): a, 5)\n", "takes at most 2 arguments"),
 ("println(1, 2)\n", "the first is the stream to write to"),
 ("x = \"s\"\nprint(x, 3)\n", "`print` can't take (String, Int)"),
 ("println(1, 2, 3)\n", "`println` takes at most 2 arguments, but 3 given"),
 ("fn many[T](xs: Seq[T]) Int:\n  1\n", "`Seq` is not a type you can write"),
 ("x = map(5, 7)\n", "{List, Array, Set, Ring, Stream} of T"),
 ("fn total[T: Monoid](xs: List[T]) T:\n  fold_all(xs)\nprintln(total(List(1, 2)))\n", "doesn't implement `Monoid`"),
 ("tuple Box[T]:\n  items: List[T]\na: Box[Int] = Box(items: List(1, \"a\"))\n", "must share one type"),
 ("tuple Box[T]:\n  items: List[T]\nfn mk() Box[Int]:\n  Box(items: List(1, \"a\"))\n", "must share one type"),
 ("a = 5s\nprintln(a + 1)\n", "cannot apply `+` to `Duration` and `Int`"),
 ("a = 5s\nprintln(a < 2)\n", "cannot compare `Duration` and `Int`"),
 ("a = 5s\nprintln(a / 2s)\n", "cannot apply `/` to `Duration` and `Duration`"),
 ("a = 5s\nprintln(a * a)\n", "cannot apply `*` to `Duration` and `Duration`"),
 ("a = 5s\nprintln(a + \"x\")\n", "cannot apply `+`"),
 ("enum Shape:\n  Circle(r: List[Int])\n  Pt\na = Shape.Circle(r: List(1, \"a\"))\n", "must share one type"),
 ("tuple Box[T]:\n  items: List[T]\nc = Box(items: List(1, \"a\"))\n", "must share one type"),
 ("fn bad1() Result[List[Int], String]:\n  Ok(List(1, \"a\"))\n", "must share one type"),
 ("c = Ok(List(1, \"a\"))\n", "must share one type"),
 ("d = List(List(1, \"a\"))\n", "must share one type"),
 ("tuple Plain:\n  ids: List[Int]\np = Plain(ids: List(1, \"a\"))\n", "must share one type"),
 ("y = List(1, \"a\").map((x): x)\n", "must share one type"),
 ("fn mk() List[Int]:\n  List(1, \"a\")\n", "must share one type"),
 ("x = Dict(1: 2).map((a, b, c): a)\n", "takes 3 parameters"),
 ("x = Dict(1: 2, 3: \"s\")\n", "values of `Dict(...)` must share one type"),
 ("y = Dict(1: 2)\nz: Dict[String, Int] = y\n", "mismatched types"),
 ("d: Dict[Int, Int] = Dict(1: 2)\nx = d |> map((a, b, c): a)\n", "takes 3 parameters"),
 ("x = List((1, 2)).map((a, b, c): a)\n", "takes 3 parameters"),
 ("x = List(1, 2).filter((a, b): true)\n", "takes 2 parameters"),
 ("x = map_all((a, b, c): a, Ok(1), Ok(2))\n", "takes 3"),
]
GOOD = [
 "enum Shape:\n  Circle(r: Int)\n  Sq(s: Int)\nxs = List(Circle(1), Sq(2))\nys = List(1, 2.5)\nzs = List(Ok(1), Err(\"x\"))\nprintln(len(xs) + len(ys) + len(zs))\n",
 "x = List(1, 2).map((a): a + 1) |> collect()\nprintln(x)\n",
 "x = reduce(0, (a, b): a + b, List(1, 2))\nprintln(x)\n",
 "d: Dict[Int, Int] = Dict(1: 2)\nx = d |> map((k, v): k) |> collect()\nprintln(x)\n",
 "x = List((1, 2)).map((a, b): a) |> collect()\nprintln(x)\n",
 "x = Ok((1, 2)).map((a, b): a)\nprintln(x)\n",
 "tuple Box:\n  tags: List[Int | String]\nfn ok1() Result[List[Int | String], String]:\n  Ok(List(1, \"a\"))\nfn nest1() List[List[Int | String]]:\n  List(List(1, \"a\"), List(2))\nb = Box(tags: List(1, \"a\"))\nprintln(len(b.tags) + len(nest1()))\n",
 "enum Shape:\n  Wide(w: List[Int | String])\n  Pt\ntuple Box[T]:\n  items: List[T]\nb = Shape.Wide(w: List(1, \"a\"))\nd: Box[Int | String] = Box(items: List(1, \"a\"))\ne = Box(items: List(1, 2))\nprintln(len(d.items))\n",
 "a = 5s\nb = a + 2s - 1s\nc = b * 3\nd = c / 2\nprintln(d < 20s and nanos(a) / nanos(2s) == 2)\n",
 "fn total[T: Monoid](xs: List[T]) T:\n  fold_all(xs)\nprintln(total(List(Sum(1), Sum(2))))\n",
 "tuple Box[T]:\n  items: List[T]\nb: Box[Int | String] = Box(items: List(1, \"a\"))\nprintln(len(b.items))\n",
 "tuple Seq:\n  n: Int\nx: Seq = Seq(n: 1)\nprintln(x.n)\n",
 "println()\nprintln(stdout, \"x\")\nassert(true, \"fine\")\nx = List(1, 2) |> map((a): a + 1) |> collect()\nprintln(max(1, 2) + len(x))\n",
 "tuple Seq[T]:\n  items: List[T]\nfn first_of(s: Seq[Int]) Int:\n  s.items |> reduce(0, (a, b): a + b)\nprintln(first_of(Seq(items: List(1, 2, 3))))\n",
 "xs = List(1, 2, 3)\nprintln(any((x): x > 2, xs))\n",
 "println(parse_number(\"1,5\", Locale.de_de))\nprintln(parse_number(\"3\"))\n",
 "fn take(xs: List[Int | String]) Int:\n  len(xs)\nfn mk() List[Int | String]:\n  List(1, \"a\")\nprintln(take(List(1, \"a\")) + len(mk()))\n",
 "xs: List[Int | String] = List(1, \"a\")\nd: Dict[String, Int | Bool] = Dict(\"n\": 1, \"on\": true)\nprintln(len(xs) + len(d))\n",
 "x = Dict(1: 2).map((k, v): k) |> collect()\ny = Dict(\"a\": 1, b: 2)\nz = Dict((5, 6), (7, 8))\nprintln(len(y) + len(z))\n",
 "x = Ok(1).map((a): a + 1)\nprintln(x)\n",
 "n = 7\nfn half(x: Double) Double:\n  x / 2.0\nprintln(half(7))\nprintln(half(cast[Double](n)))\nz: Double = 3\n",
]
fails = 0
def chk(src, *flags):
    open("/tmp/_gap.mx", "w").write(src)
    return subprocess.run([sys.executable, "-m", "moxie", *flags, "check", "/tmp/_gap.mx"], capture_output=True, text=True)
for flags in ((), ("--gc",)):
    for src, msg in BAD:
        r = chk(src, *flags)
        if msg not in r.stdout + r.stderr:
            fails += 1; print("FAIL bad", flags, repr(src), r.stdout, r.stderr)
    for src in GOOD:
        r = chk(src, *flags)
        if r.returncode:
            fails += 1; print("FAIL good", flags, repr(src), r.stdout, r.stderr)
print("checker gaps: FAIL" if fails else "checker gaps: ok")
