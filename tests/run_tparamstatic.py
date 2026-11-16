"""`R.f(args)` on a type parameter bounded by an interface: checked against the member's signature.  Run: python3 tests/run_tparamstatic.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
EXPR = "interface Expr\n  static fn lit(n Int) Self,\n  static fn add(a Self, b Self) Self\n"
MUL = "interface Mul\n  static fn mul(a Self, b Self) Self\n"
SYM = ("interface Sym[R[_]]\n  static fn lit(n Int) R[Int],\n  static fn bool(b Bool) R[Bool],\n  static fn add(a R[Int], b R[Int]) R[Int],\n"
       "  static fn leq(a R[Int], b R[Int]) R[Bool],\n  static fn cond[A](c R[Bool], t R[A], e R[A]) R[A]\n")
GOOD = [
 ("a plain bound", EXPR + "fn f[R Expr]() R\n  R.add(R.lit(1), R.lit(2))\n"),
 ("two bounds", EXPR + MUL + "fn f[R Expr + Mul](x R) R\n  R.add(R.mul(x, x), R.lit(1))\n"),
 ("a constructor class", SYM + "fn f[R[_] Sym]() R[Int]\n  R.cond(R.leq(R.lit(1), R.lit(2)), R.add(R.lit(10), R.lit(5)), R.lit(0))\n"),
 ("a generic member at two types", SYM + "fn f[R[_] Sym]() R[Bool]\n  R.cond(R.leq(R.lit(1), R.lit(2)), R.bool(true), R.bool(false))\n"),
 ("a parameter of the type", EXPR + "fn f[R Expr](a R, b R) R\n  R.add(a, b)\n"),
 ("a call with an unknown argument is not an error", EXPR + "fn f[R Expr](xs List[Int]) R\n  R.add(R.lit(xs(0)), R.lit(len(xs)))\n"),
]
BAD = [
 ("an Int where Self is wanted", EXPR + "fn f[R Expr]() R\n  R.add(R.lit(1), 5)\n", "expected `R`, found `Int`"),
 ("a String where an Int is wanted", EXPR + "fn f[R Expr]() R\n  R.lit(\"x\")\n", "expected `Int`, found `String`"),
 ("R[Bool] where R[Int] is wanted", SYM + "fn f[R[_] Sym]() R[Int]\n  R.add(R.lit(1), R.bool(true))\n", "expected `R[Int]`, found `R[Bool]`"),
 ("a number as the test of cond", SYM + "fn f[R[_] Sym]() R[Int]\n  R.cond(R.lit(1), R.lit(2), R.lit(3))\n", "expected `R[Bool]`, found `R[Int]`"),
 ("branches of different types", SYM + "fn f[R[_] Sym]() R[Int]\n  R.cond(R.leq(R.lit(1), R.lit(2)), R.lit(1), R.bool(true))\n", "found `R[Bool]`"),
 ("a different type parameter", EXPR + "fn f[R Expr, S Expr](x S) R\n  R.add(x, R.lit(1))\n", "expected `R`, found `S`"),
]
fails = []
def run(src, cmd="check"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
for name, src in GOOD:
    rc, o = run(src)
    ok = rc == 0
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> {o.strip()[:240]}"))
    if not ok: fails.append(name)
for name, src, word in BAD:
    rc, o = run(src)
    ok = rc != 0 and word in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> rc={rc} {o.strip()[:240]}"))
    if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
