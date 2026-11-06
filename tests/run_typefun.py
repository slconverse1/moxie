"""Type functions: `type alias F[T] = when T: pattern -> type`, matching, recursion, numbers, fuel.  Run: python3 tests/run_typefun.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ELEM = 'type alias Elem[T] = when T:\n  List[X] -> X\n  Array[X][N] -> X\n'
CONCAT = 'type alias Concat[A, B] = when A:\n  () -> B\n  (H, ...T) -> (H, ...Concat[T, B])\n'
LENGTH = 'type alias Length[T] = when T:\n  () -> 0\n  (H, ...Rest) -> 1 + Length[Rest]\n'
SHRINK = 'type alias Shrink[T] = when T:\n  Array[X][N] -> Array[X][N - 1]\n'
BOX = 'tuple Box[T]:\n  v: T\n'
BAD = [
 ("Elem of a List", ELEM + 'a: Elem[List[String]] = 3\n', "expected `String`, found `Int`"),
 ("Elem of an Array", ELEM + 'a: Elem[Array[Int][3]] = "s"\n', "expected `Int`, found `String`"),
 ("no arm matches", ELEM + BOX + 'a: Elem[Box[Int]] = 3\n', "no arm of `Elem` matches `Box[Int]`"),
 ("Concat joins tuple types", CONCAT + 'd: Concat[(Int, String), (Bool,)] = (1, "a", 2)\n', "expected `(Int, String, Bool)`, found `(Int, String, Int)`"),
 ("Length gives a size", LENGTH + 'b: Array[Int][Length[(Int, String, Bool)]] = Array(1, 2)\n', "expected `Array[Int][3]`, found `Array[Int][2]`"),
 ("size arithmetic in a result", SHRINK + 'd: Shrink[Array[Int][3]] = Array(1, 2, 3)\n', "expected `Array[Int][2]`, found `Array[Int][3]`"),
 ("a stuck type is only itself", ELEM + 'fn f[C](x: C) Elem[C]:\n  x\n', "expected `Elem[C]`, found `C`"),
 ("a type function in a result type", ELEM + 'fn f(xs: List[Int]) Elem[List[Int]]:\n  "s"\n', "expected `Int`, found `String`"),
 ("the fuel stops a runaway", 'type alias Spin[T] = when T:\n  X -> Spin[(X, X)]\ns: Spin[Int] = 1\n', "grew past the size limit"),
 ("the fuel stops a slow one", 'type alias Count[T] = when T:\n  X -> Count[Array[X][1]]\ns: Count[Int] = 1\n', "did not finish in 64 reductions"),
 ("an arm that does not shrink is warned about", 'type alias Spin[T] = when T:\n  X -> Spin[(X, X)]\n', "which is not a piece of what its arm matched"),
]
GOOD = [
 ("Elem of a List", ELEM + 'a: Elem[List[String]] = "s"\nprintln(a)\n', "s"),
 ("Elem in a result type", ELEM + 'fn head_of(xs: Array[Int][3]) Elem[Array[Int][3]]:\n  xs(0)\nprintln(head_of(Array(7, 8, 9)))\n', "7"),
 ("Concat of tuple types", CONCAT + 'e: Concat[(Int, String), (Bool,)] = (1, "a", true)\nprintln(e)\n', "1"),
 ("Concat in a generic function", CONCAT + 'fn pair_up[T](x: T) Concat[(T,), (Int,)]:\n  (x, 0)\nprintln(pair_up("a"))\n', "a"),
 ("Length as a size", LENGTH + 'b: Array[Int][Length[(Int, String)]] = Array(1, 2)\nprintln(b(1))\n', "2"),
 ("size arithmetic", SHRINK + 'c: Shrink[Array[Int][3]] = Array(1, 2)\nprintln(c(1))\n', "2"),
 ("an arm that shrinks gets no warning", LENGTH + 'println("ok")\n', "ok"),
]
fails = []


def run(cmd, src):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout.decode() + r.stderr.decode()


for name, src, want in BAD:
    rc, o = run("check", src)
    ok = want in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {o[:400]!r}"))
    if not ok:
        fails.append(name)
for name, src, want in GOOD:
    rc, o = run("run", src)
    ok = rc == 0 and want in o and "warning" not in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {o[:400]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
