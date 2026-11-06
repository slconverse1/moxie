"""Checker coverage of generics: bounds in bodies, one type per parameter, type-argument counts.  Run: python3 tests/run_generics.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BAD = [
 ("< on an unbounded T", 'fn smaller[T](a: T, b: T) Bool:\n  a < b\nprintln(smaller(1, 2))\n', "needs a `Ordered` bound"),
 ("== on an unbounded T", 'fn same[T](a: T, b: T) Bool:\n  a == b\nprintln(same(1, 2))\n', "needs a `Equatable` bound"),
 ("+ on a T that is only Ordered", 'fn add[T: Ordered](a: T, b: T) T:\n  a + b\nprintln(add(1, 2))\n', "needs a `Addable` bound"),
 ("* on a T that is only Addable", 'fn dbl[T: Addable](a: T) T:\n  a * a\nprintln(dbl(2))\n', "needs a `Numeric` bound"),
 ("one T bound to two types", 'fn pick[T](a: T, b: T) T: a\nprintln(pick(1, "x"))\n', "needs one type for `T`"),
 ("a result type that follows T", 'fn first[T](a: T, b: T) T: a\nx: Int = first("a", "b")\nprintln(x)\n', "expected"),
 ("too few type arguments", 'tuple Pair[A, B]:\n  a: A\n  b: B\nfn f(p: Pair[Int]) Int: 1\n', "takes 2 type arguments, but 1 given"),
 ("too many type arguments", 'tuple Box[T]:\n  v: T\nfn f(p: Box[Int, Int]) Int: 1\n', "takes 1 type argument, but 2 given"),
 ("too many in a return type", 'enum Opt[T]:\n  Some(T)\n  Nothing\nfn f() Opt[Int, Int]: Nothing\n', "takes 1 type argument, but 2 given"),
]
GOOD = [
 ("Ordered gives <", 'fn smaller[T: Ordered](a: T, b: T) Bool:\n  a < b\nprintln(smaller(1, 2))\n', "true"),
 ("Equatable gives ==", 'fn same[T: Equatable](a: T, b: T) Bool:\n  a == b\nprintln(same("a", "a"))\n', "true"),
 ("Hashable includes ==", 'fn same[T: Hashable](a: T, b: T) Bool:\n  a == b\nprintln(same(1, 1))\n', "true"),
 ("Numeric gives + - * /", 'fn f[T: Numeric](a: T, b: T) T:\n  a * b - a + b / b\nprintln(f(3, 4))\n', "10"),
 ("several bounds", 'fn mx[T: Ordered + Show](a: T, b: T) String:\n  if a < b: "${b}" else: "${a}"\nprintln(mx(2, 9))\n', "9"),
 ("Int and Float arguments for one T", 'fn first[T](a: T, b: T) T: a\nprintln(first(1, 2.5))\n', "1"),
 ("passing and returning need no bound", 'fn id[T](a: T) T: a\nprintln(id("hi"))\n', "hi"),
 ("the right number of type arguments", 'tuple Pair[A, B]:\n  a: A\n  b: B\nfn f(p: Pair[Int, String]) Int: p.a\nprintln(f(Pair(7, "x")))\n', "7"),
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
