"""The checker's types for generic values: applications, sizes, calls that fix type parameters.  Run: python3 tests/run_ctypes.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOX = 'tuple Box[T]\n  v T\n'
BAD = [
 ("a Box[Int] built from a String", BOX + 'b Box[Int] = Box(v: "not an int")\n', "expected `Box[Int]`, found `Box[String]`"),
 ("array size mismatch", 'x Array[Int][3] = Array(1, 2)\n', "expected `Array[Int][3]`, found `Array[Int][2]`"),
 ("array element mismatch", 'x Array[String][2] = Array(1, 2)\n', "expected `Array[String][2]`, found `Array[Int][2]`"),
 ("generic result flows into the wrong type", 'fn first[T](xs List[T]) T = xs(0)\ny Int = first(List("a", "b"))\n', "expected `Int`, found `String`"),
 ("a wrapper's type follows its argument", BOX + 'fn wrap[T](x T) Box[T]\n  Box(v: x)\nz Box[Int] = wrap("s")\n', "expected `Box[Int]`, found `Box[String]`"),
 ("two lists for one T", 'fn same[T](a List[T], b List[T]) Int = 1\nw Int = same(List(1), List("a"))\n', "`same` needs one type"),
 ("a field of a Box[String] is a String", BOX + 'fn f(b Box[String]) Int\n  n Int = b.v\n  n\n', "expected `Int`, found `String`"),
 ("Ok of the wrong type in a Result", 'fn g() Result[Int, String]\n  Ok("x")\n', "expected `Result[Int, String]`"),
 ("a list where a Box goes", BOX + 'fn f(b Box[Int]) Int = 1\nprintln(f(List(1)))\n', "expected `Box[Int]`, found `List[Int]`"),
 ("a lambda's result fixes U", 'fn app2[T, U](x T, f (T) -> U) U = f(x)\na String = app2(3, (n) -> n + 1)\n', "expected `String`, found `Int`"),
 ("a lambda's parameter takes T from the first argument", 'fn app2[T, U](x T, f (T) -> U) U = f(x)\nb Int = app2("s", (s) -> s + 1)\n', "cannot apply `+` to `String` and `Int`"),
 ("a lambda of the wrong result type for a function parameter", 'fn twice(f (Int) -> Int, x Int) Int = f(f(x))\ne Int = twice((n) -> "x", 4)\n', "expected `(Int) -> Int`, found `(Int) -> String`"),
 ("a constructor parameter F[_] fixes the wrapper", BOX + 'fn lift[F[_], A](x F[A]) F[A] = x\na Box[Int] = lift(Box(v: "s"))\n', "expected `Box[Int]`, found `Box[String]`"),
 ("A from F[A]", BOX + 'fn unbox[F[_], A](x F[A]) A = x.v\nb Int = unbox(Box(v: "s"))\n', "expected `Int`, found `String`"),
 ("a type lambda applied in a type", 'fn f() ([A] -> Result[A, String])[Int]\n  Ok("x")\n', "expected `Result[Int, String]`"),
 ("len gives an Int", 'n String = len(Array(1, 2))\n', "expected `String`, found `Int`"),
 ("a predicate gives a Bool", 'b Int = starts_with("a", "b")\n', "expected `Int`, found `Bool`"),
 ("map then collect keeps the element type", 'xs = List(1, 2, 3)\na List[String] = xs |> map((x) -> x + 1) |> collect()\n', "expected `List[String]`, found `List[Int]`"),
 ("map with the function first", 'xs = List(1, 2, 3)\nb Int = map((x) -> x + 1, xs)\n', "expected `Int`, found `List[Int]`"),
 ("map over a stream is a stream", 'xs = List(1, 2, 3)\nb Int = map((x) -> x + 1, to_stream(xs))\n', "expected `Int`, found `Stream[Int]`"),
 ("a method call is a pipe", 'xs = List(1, 2, 3)\na List[String] = xs.map((x) -> x + 1).collect()\n', "expected `List[String]`, found `List[Int]`"),
 ("a lambda parameter takes the element type", 'xs = List(1, 2, 3)\nn Int = xs |> map((x) -> x + "a") |> count()\n', "cannot apply `+` to `Int` and `String`"),
 ("upper of a String is a String", 'h Int = upper("a")\n', "expected `Int`, found `String`"),
 ("map over a Result", 'r Result[Int, String] = Ok(1)\nn Int = map((x) -> x + 1, r)\n', "expected `Int`, found `Result[Int, String]`"),
 ("T returned as an Int", 'fn bad[T](x T) Int\n  x\n', "expected `Int`, found `T`"),
 ("an Int returned as T", 'fn bad[T](x T) T\n  1\n', "expected `T`, found `Int`"),
 ("a List[T] returned as List[Int]", 'fn bad[T](xs List[T]) List[Int]\n  xs\n', "expected `List[Int]`, found `List[T]`"),
 ("one parameter returned as another", 'fn bad[T, U](x T, y U) T\n  y\n', "expected `T`, found `U`"),
 ("a method the bound does not give", 'interface Speaker\n  fn speak() String\ninterface Loud\n  Speaker,\n  fn shout() String\nfn bad[T Speaker](x T) String\n  x.shout()\n', "`shout` is not provided by the bound of `T` (Speaker)"),
 ("a field of a plain T", 'fn bad[T](x T) String\n  x.name\n', "`T` has no bound, so `name` is not available on it"),
 ("a predicate that does not return Bool", 'xs = List(1, 2)\nn = xs |> filter((x) -> x + 1) |> count()\n', "`filter` can't take ((Int) -> Int, List[Int])"),
 ("a String where take wants an Int", 'xs = List(1, 2)\nb = take("a", xs)\n', "`take` can't take (String, List[Int])"),
 ("upper of an Int", 'e = upper(3)\n', "`upper` can't take (Int)"),
 ("a literal returned as the wrong type", 'fn g() Int = "s"\n', "expected `Int`, found `String`"),
]
GOOD = [
 ("Box[Int] built from an Int", BOX + 'b Box[Int] = Box(v: 3)\nprintln(b.v + 1)\n', "4"),
 ("Box[Double] from an Int", BOX + 'b Box[Double] = Box(v: 3)\nprintln(b.v)\n', "3"),
 ("lambda inference accepts a good program", 'fn app2[T, U](x T, f (T) -> U) U = f(x)\nc Int = app2(3, (n) -> n + 1)\nprintln(c)\n', "4"),
 ("a constructor parameter in a good call", BOX + 'fn lift[F[_], A](x F[A]) F[A] = x\nb Box[String] = lift(Box(v: "s"))\nprintln(b.v)\n', "s"),
 ("a user's own len is not the builtin", 'fn len(x String) String = x\ns String = len("ab")\nprintln(s)\n', "ab"),
 ("a pipeline checks and runs", 'xs = List(1, 2, 3)\nys List[Int] = xs |> map((x) -> x * 2) |> collect()\nprintln(ys |> sum())\n', "12"),
 ("upper of a Char is a Char", "c Char = upper('a')\nprintln(c)\n", "A"),
 ("a user type with its own map is left alone", BOX + 'fn map[A, B](f (A) -> B, b Box[A]) Box[B]\n  Box(v: f(b.v))\nz Box[Int] = map((x) -> x + 1, Box(v: 1))\nprintln(z.v)\n', "2"),
 ("T passed on, returned, and stored", 'fn id[T](x T) T\n  x\nfn one[T](x T) List[T]\n  List(id(x))\nfn keep[T](xs List[T]) List[T]\n  xs\nprintln(len(keep(one(3))))\n', "1"),
 ("a bounded T used with its operators", 'fn dbl[T Numeric](x T) T\n  x + x\nprintln(dbl(2))\n', "4"),
 ("a method the bound gives, through an embedded interface", 'interface Speaker\n  fn speak() String\ninterface Loud\n  Speaker,\n  fn shout() String\nfn ok[T Loud](x T) String\n  x.speak()\nprintln("ok")\n', "ok"),
 ("a function called as a method on a T", 'fn same[T](x T) Int\n  x.len()\nprintln("ok")\n', "ok"),
 ("sizes agree", 'x Array[Int][2] = Array(1, 2)\nprintln(x(1))\n', "2"),
 ("a generic function with a wrapper", BOX + 'fn wrap[T](x T) Box[T]\n  Box(v: x)\nz Box[String] = wrap("s")\nprintln(z.v)\n', "s"),
 ("first of a list", 'fn first[T](xs List[T]) T = xs(0)\ny String = first(List("a", "b"))\nprintln(y)\n', "a"),
 ("Ok and Err in a Result", 'fn g(n Int) Result[Int, String]\n  if n > 0 then Ok(n) else Err("no")\nprintln(g(1))\n', "Ok"),
 ("a variadic parameter is an Array in the body", 'fn count(xs ...Int) Int\n  len(xs)\nprintln(count(1, 2, 3))\n', "3"),
]
fails = []


def run(cmd, src):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    return r.returncode, r.stdout.decode() + r.stderr.decode()


for name, src, want in BAD:
    rc, o = run("check", src)
    ok = rc != 0 and want in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {o[:300]!r}"))
    if not ok:
        fails.append(name)
for name, src, want in GOOD:
    rc, o = run("run", src)
    ok = rc == 0 and want in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {o[:300]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
