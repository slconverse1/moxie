"""`read[T]` for `deriving read` tuples: names, positions, nested tuples, and an Err (never a silent value or a crash) for a missing, unknown, repeated, or wrongly typed field.  Run: python3 tests/run_read.py"""
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

DECL = 'tuple Point deriving read, show:\n  x: Int\n  y: Int\ntuple Customer deriving read, show:\n  name: String\n  vip: Bool\ntuple Order deriving read, show:\n  customer: Customer\n  total: Int\n'

case('a flat tuple reads with names', DECL + 'println(read[Point]("Point(x: 1, y: 2)"))' + '\n', 0, 'Ok(Point(x: 1, y: 2))')
case('a flat tuple reads by position', DECL + 'println(read[Point]("Point(1, 2)"))' + '\n', 0, 'Ok(Point(x: 1, y: 2))')
case('a missing field is an Err', DECL + 'println(read[Point]("Point(x: 1)"))' + '\n', 0, 'missing field `y`')
case('an unknown field is an Err', DECL + 'println(read[Point]("Point(x: 1, z: 2)"))' + '\n', 0, '`z` is not a field')
case('a repeated field is an Err', DECL + 'println(read[Point]("Point(x: 1, y: 2, x: 3)"))' + '\n', 0, 'field `x` is given twice')
case('a wrong scalar is an Err', DECL + 'println(read[Point]("Point(x: 1, y: abc)"))' + '\n', 0, 'field `y`')
case('a nested tuple reads', DECL + 'println(read[Order]("Order(customer: Customer(name: \\"Ann\\", vip: true), total: 30)"))' + '\n', 0, 'Ok(Order(customer: Customer(name: "Ann", vip: true), total: 30))')
case('a nested missing field names its path', DECL + 'println(read[Order]("Order(customer: Customer(name: \\"Ann\\"), total: 30)"))' + '\n', 0, 'field `customer`: missing field `vip`')
case('a nested wrong type names its path', DECL + 'println(read[Order]("Order(customer: Customer(name: \\"Ann\\", vip: 3), total: 30)"))' + '\n', 0, 'field `customer`: field `vip`')

print(f"{len(fails)} failed" if fails else "all passed")
sys.exit(1 if fails else 0)
