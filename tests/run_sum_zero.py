"""An empty stream sums to its element type's zero (and multiplies to its one).  Run: python3 tests/run_sum_zero.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=()):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", *flags, "run", f.name], cwd=ROOT, capture_output=True, timeout=120)
        out = r.stdout.decode() + r.stderr.decode()
    except subprocess.TimeoutExpired:
        out = "TIMEOUT"
    os.unlink(f.name)
    return out

MONEY = """tuple Money deriving show:
  cents: Int
impl Money:
  fn + (other: Money) Money:
    Money(cents: cents + other.cents)
  static fn zero() Money:
    Money(cents: 0)
  static fn one() Money:
    Money(cents: 1)
"""
CASES = [
 ("empty Float sum is 0.0", "fn t(xs: List[Float]) Float:\n  xs |> sum()\nprintln(t(List()))\n", "0.0"),
 ("empty Float product is 1.0", "fn t(xs: List[Float]) Float:\n  xs |> product()\nprintln(t(List()))\n", "1.0"),
 ("empty Int sum is 0", "fn t(xs: List[Int]) Int:\n  sum(xs)\nprintln(t(List()))\n", "0"),
 ("empty String sum is the empty string", "fn t(xs: List[String]) String:\n  xs.sum()\nprintln(\"[${t(List())}]\")\n", "[]"),
 ("empty Money sum is Money's zero", MONEY + "fn t(xs: List[Money]) Money:\n  xs.sum()\nprintln(t(List()))\n", "Money(cents: 0)"),
 ("empty Money product is Money's one", MONEY + "fn t(xs: List[Money]) Money:\n  xs |> product()\nprintln(t(List()))\n", "Money(cents: 1)"),
 ("an empty list written with its type", MONEY + "println(List[Money]() |> sum())\nprintln(List[Float]() |> sum())\n", "Money(cents: 0)\n0.0"),
 ("a Dict mapped to values sums to 0.0", "fn t(d: Dict[String, Float]) Float:\n  d |> map((k, v): v) |> sum()\nprintln(t(Dict()))\n", "0.0"),
 ("a generic function mapped over an empty list", "fn ident[T](x: T) T:\n  x\nfn u(xs: List[Float]) Float:\n  xs |> map(ident) |> product()\nprintln(u(List()))\n", "1.0"),
 ("a range filtered to nothing", "fn t(n: Int) Float:\n  (1..n) |> filter(_ > n) |> map(_ * 1.5) |> sum()\nprintln(t(3))\n", "0.0"),
 ("a full list still adds", MONEY + "println(List(Money(cents: 1), Money(cents: 2)) |> sum())\nprintln(List(1.5, 2.0) |> sum())\n", "Money(cents: 3)\n3.5"),
]
fails = []
for name, src, want in CASES:
    for flags in ((), ("--gc",)):
        out = run(src, flags).strip()
        ok = out == want
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if flags else "") + ("" if ok else f"  {out[:200]!r}"))
        if not ok:
            fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
