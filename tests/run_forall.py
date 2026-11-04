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
 ("a function type has no generator", 'test "t":\n  forall f: (Int) -> Int:\n    assert(true)\n', [], 1, "cannot generate"),
]
fails = []
for name, src, flags, rc_want, out_w in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = "check" if "pure" in name or "belongs" in name else "test"
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
