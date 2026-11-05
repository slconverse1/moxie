"""Property test (forall) tests.  Run: python3 tests/run_forall.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REV = 'xs |> to_stream() |> reverse() |> reverse() |> collect()'
CASES = [
 ("a true property passes", f'test "rev":\n  forall xs: List[Int]:\n    assert_eq({REV}, xs)\n', [], 0, "ok    rev"),
 ("several names", 'test "two":\n  forall a: Int8, b: Bool, s: String:\n    assert(len(s) >= 0)\n', [], 0, "ok    two"),
 ("an integer shrinks to the boundary", 'test "t":\n  forall x: Int:\n    assert(x < 1000, "big")\n', [], 1, "x = 1000"),
 ("a list shrinks to its smallest failing form", 'test "t":\n  forall xs: List[Int]:\n    assert(len(xs) < 3, "long")\n', [], 1, "xs = List(0, 0, 0)"),
 ("a string shrinks", 'test "t":\n  forall s: String:\n    assert(len(s) < 4, "long")\n', [], 1, 's = "'),
 ("a tuple type", 'test "t":\n  forall p: (Int, Bool):\n    assert(p(0) < 5, "x")\n', [], 1, "p = (5, "),
 ("a declared tuple", 'tuple Pt:\n  x: Int\n  y: Int\n\ntest "t":\n  forall p: Pt:\n    assert(p.x < 7, "x")\n', [], 1, "x: 7"),
 ("an enum", 'enum Shape:\n  Dot\n  Box(w: Int)\n\ntest "t":\n  forall s: Shape:\n    assert(s ~= Shape.Dot, "dot")\n', [], 1, "Dot"),
 ("the failure prints the seed", 'test "t":\n  forall x: Int:\n    assert(x < 0, "pos")\n', [], 1, "seed 20260101"),
 ("--seed changes the run and is echoed", 'test "t":\n  forall x: Int:\n    assert(x < 0, "pos")\n', ["--seed", "7"], 1, "seed 7"),
 ("--cases limits the run", 'test "t":\n  forall x: Int:\n    assert(false, "no")\n', ["--cases", "1"], 1, "of 1 "),
 ("the same seed replays", 'test "t":\n  forall x: Int:\n    assert(x < 1000, "big")\n', ["--seed", "5"], 1, "case "),
 ("the body must be pure", 'test "t":\n  forall x: Int:\n    println(x)\n', [], 1, "must be pure"),
 ("forall belongs in a test", 'fn f() Unit:\n  forall x: Int:\n    assert(true)\n', [], 1, "inside a test"),
 ("a mixer-written Generatable keeps its rule", 'tuple Pct:\n  n: Int\n\nimpl Generatable for Pct:\n  static fn generate(g: Gen) Self: Pct(gen_int(g, 0, 100))\n  fn shrink() List[Pct]:\n    when n:\n      0 -> List()\n      _ -> List(Pct(0), Pct(n - 1))\n\ntest "t":\n  forall p: Pct:\n    assert(p.n >= 0 and p.n <= 100)\n', [], 0, "ok    t"),
 ("a mixer-written shrink is used", 'tuple Pct:\n  n: Int\n\nimpl Generatable for Pct:\n  static fn generate(g: Gen) Self: Pct(gen_int(g, 0, 100))\n  fn shrink() List[Pct]:\n    when n:\n      0 -> List()\n      _ -> List(Pct(0), Pct(n - 1))\n\ntest "t":\n  forall p: Pct:\n    assert(p.n < 10, "big")\n', [], 1, "Pct(n: 10)"),
 ("Generatable values nest inside other types", 'tuple Pct:\n  n: Int\n\nimpl Generatable for Pct:\n  static fn generate(g: Gen) Self: Pct(gen_int(g, 0, 100))\n  fn shrink() List[Pct]:\n    when n:\n      0 -> List()\n      _ -> List(Pct(0), Pct(n - 1))\n\ntest "t":\n  forall xs: List[Pct]:\n    assert(len(xs) < 3, "long")\n', [], 1, "xs = List(Pct("),
 ("sample builds a value inside generate", 'tuple Sorted:\n  items: List[Int]\n\nimpl Generatable for Sorted:\n  static fn generate(g: Gen) Self:\n    xs = sample[List[Int8]](g)\n    Sorted(xs |> to_stream() |> sort() |> collect())\n\ntest "t":\n  forall s: Sorted:\n    assert_eq(s.items |> to_stream() |> sort() |> collect(), s.items)\n', [], 0, "ok    t"),
 ("gen_pick chooses from a list", 'tuple Day:\n  name: String\n\nimpl Generatable for Day:\n  static fn generate(g: Gen) Self: Day(gen_pick(g, List("Mon", "Tue")))\n\ntest "t":\n  forall d: Day:\n    assert(d.name == "Mon" or d.name == "Tue")\n', [], 0, "ok    t"),
 ("an invariant filters the built-in generator", 'tuple Person:\n  name: String\n  invariant len(name) > 0\n\ntest "t":\n  forall p: Person:\n    assert(len(p.name) > 0)\n', [], 0, "ok    t"),
 ("an impossible invariant is reported", 'tuple Never:\n  n: Int\n  invariant n ~= n\n\ntest "t":\n  forall x: Never:\n    assert(true)\n', [], 1, "write impl Generatable"),
 ("signature: generate must be static", 'tuple P:\n  n: Int\n\nimpl Generatable for P:\n  fn generate(g: Gen) Self: P(1)\n', [], 1, "must be `static`"),
 ("signature: generate takes a Gen", 'tuple P:\n  n: Int\n\nimpl Generatable for P:\n  static fn generate(g: Int) Self: P(1)\n', [], 1, "parameter of type Gen"),
 ("signature: generate returns Self", 'tuple P:\n  n: Int\n\nimpl Generatable for P:\n  static fn generate(g: Gen) Int: 1\n', [], 1, "must return Self"),
 ("signature: generate is required", 'tuple P:\n  n: Int\n\nimpl Generatable for P:\n  fn shrink() List[P]: List()\n', [], 1, "needs `static fn generate"),
 ("signature: shrink returns List of Self", 'tuple P:\n  n: Int\n\nimpl Generatable for P:\n  static fn generate(g: Gen) Self: P(1)\n  fn shrink() List[Int]: List()\n', [], 1, "must return List[Self]"),
 ("signature: shrink takes nothing", 'tuple P:\n  n: Int\n\nimpl Generatable for P:\n  static fn generate(g: Gen) Self: P(1)\n  fn shrink(k: Int) List[P]: List()\n', [], 1, "takes no parameters"),
 ("signature: shrink may return List[Self]", 'tuple P:\n  n: Int\n\nimpl Generatable for P:\n  static fn generate(g: Gen) Self: P(1)\n  fn shrink() List[Self]: List()\n', [], 0, "ok"),
 ("a function type has no generator", 'test "t":\n  forall f: (Int) -> Int:\n    assert(true)\n', [], 1, "cannot generate"),
]
fails = []
for name, src, flags, rc_want, out_w in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = "check" if "pure" in name or "belongs" in name or name.startswith("signature:") else "test"
    r = subprocess.run([sys.executable, "-m", "moxie", cmd] + (flags if cmd == "test" else []) + [f.name], cwd=ROOT, capture_output=True, timeout=120)
    os.unlink(f.name)
    rc, o = r.returncode, r.stdout.decode() + r.stderr.decode()
    ok = (rc_want is None or rc == rc_want) and out_w in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {o[:300]!r}"))
    if not ok:
        fails.append(name)
# determinism: two runs, same output
src = 'test "t":\n  forall xs: List[Int]:\n    assert(len(xs) < 4, "long")\n'
with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
    f.write(src)
outs = [subprocess.run([sys.executable, "-m", "moxie", "test", f.name], cwd=ROOT, capture_output=True).stdout for _ in range(2)]
os.unlink(f.name)
if outs[0] == outs[1]:
    print("ok    two runs agree")
else:
    print("FAIL  two runs agree"); fails.append("determinism")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
