"""The checker's types for generic values: applications, sizes, calls that fix type parameters.  Run: python3 tests/run_ctypes.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOX = 'tuple Box[T]:\n  v: T\n'
BAD = [
 ("a Box[Int] built from a String", BOX + 'b: Box[Int] = Box(v: "not an int")\n', "expected `Box[Int]`, found `Box[String]`"),
 ("array size mismatch", 'x: Array[Int][3] = Array(1, 2)\n', "expected `Array[Int][3]`, found `Array[Int][2]`"),
 ("array element mismatch", 'x: Array[String][2] = Array(1, 2)\n', "expected `Array[String][2]`, found `Array[Int][2]`"),
 ("generic result flows into the wrong type", 'fn first[T](xs: List[T]) T: xs(0)\ny: Int = first(List("a", "b"))\n', "expected `Int`, found `String`"),
 ("a wrapper's type follows its argument", BOX + 'fn wrap[T](x: T) Box[T]:\n  Box(v: x)\nz: Box[Int] = wrap("s")\n', "expected `Box[Int]`, found `Box[String]`"),
 ("two lists for one T", 'fn same[T](a: List[T], b: List[T]) Int: 1\nw: Int = same(List(1), List("a"))\n', "`same` needs one type"),
 ("a field of a Box[String] is a String", BOX + 'fn f(b: Box[String]) Int:\n  n: Int = b.v\n  n\n', "expected `Int`, found `String`"),
 ("Ok of the wrong type in a Result", 'fn g() Result[Int, String]:\n  Ok("x")\n', "expected `Result[Int, String]`"),
 ("a list where a Box goes", BOX + 'fn f(b: Box[Int]) Int: 1\nprintln(f(List(1)))\n', "expected `Box[Int]`, found `List[Int]`"),
 ("a lambda's result fixes U", 'fn app2[T, U](x: T, f: (T) -> U) U: f(x)\na: String = app2(3, (n): n + 1)\n', "expected `String`, found `Int`"),
 ("a lambda's parameter takes T from the first argument", 'fn app2[T, U](x: T, f: (T) -> U) U: f(x)\nb: Int = app2("s", (s): s + 1)\n', "cannot apply `+` to `String` and `Int`"),
 ("a lambda of the wrong result type for a function parameter", 'fn twice(f: (Int) -> Int, x: Int) Int: f(f(x))\ne: Int = twice((n): "x", 4)\n', "expected `(Int) -> Int`, found `(Int) -> String`"),
 ("a constructor parameter F[_] fixes the wrapper", BOX + 'fn lift[F[_], A](x: F[A]) F[A]: x\na: Box[Int] = lift(Box(v: "s"))\n', "expected `Box[Int]`, found `Box[String]`"),
 ("A from F[A]", BOX + 'fn unbox[F[_], A](x: F[A]) A: x.v\nb: Int = unbox(Box(v: "s"))\n', "expected `Int`, found `String`"),
 ("a type lambda applied in a type", 'fn f() ([A] -> Result[A, String])[Int]:\n  Ok("x")\n', "expected `Result[Int, String]`"),
 ("a literal returned as the wrong type", 'fn g() Int: "s"\n', "expected `Int`, found `String`"),
]
GOOD = [
 ("Box[Int] built from an Int", BOX + 'b: Box[Int] = Box(v: 3)\nprintln(b.v + 1)\n', "4"),
 ("Box[Double] from an Int", BOX + 'b: Box[Double] = Box(v: 3)\nprintln(b.v)\n', "3"),
 ("lambda inference accepts a good program", 'fn app2[T, U](x: T, f: (T) -> U) U: f(x)\nc: Int = app2(3, (n): n + 1)\nprintln(c)\n', "4"),
 ("a constructor parameter in a good call", BOX + 'fn lift[F[_], A](x: F[A]) F[A]: x\nb: Box[String] = lift(Box(v: "s"))\nprintln(b.v)\n', "s"),
 ("sizes agree", 'x: Array[Int][2] = Array(1, 2)\nprintln(x(1))\n', "2"),
 ("a generic function with a wrapper", BOX + 'fn wrap[T](x: T) Box[T]:\n  Box(v: x)\nz: Box[String] = wrap("s")\nprintln(z.v)\n', "s"),
 ("first of a list", 'fn first[T](xs: List[T]) T: xs(0)\ny: String = first(List("a", "b"))\nprintln(y)\n', "a"),
 ("Ok and Err in a Result", 'fn g(n: Int) Result[Int, String]:\n  if n > 0: Ok(n) else: Err("no")\nprintln(g(1))\n', "Ok"),
 ("a variadic parameter is an Array in the body", 'fn count(xs: ...Int) Int:\n  len(xs)\nprintln(count(1, 2, 3))\n', "3"),
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
