"""`read[T]` for `deriving read` tuples, enums, and Lists: names, positions, nested tuples, and an Err (never a silent value or a crash) for a missing, unknown, repeated, or wrongly typed field.  Run: python3 tests/run_read.py"""
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

DECL = 'tuple Point deriving read, show\n  x Int\n  y Int\ntuple Customer deriving read, show\n  name String\n  vip Bool\ntuple Order deriving read, show\n  customer Customer\n  total Int\n'

case('a flat tuple reads with names', DECL + 'println(read[Point]("Point(x: 1, y: 2)"))' + '\n', 0, 'Ok(Point(x: 1, y: 2))')
case('a flat tuple reads by position', DECL + 'println(read[Point]("Point(1, 2)"))' + '\n', 0, 'Ok(Point(x: 1, y: 2))')
case('a missing field is an Err', DECL + 'println(read[Point]("Point(x: 1)"))' + '\n', 0, 'missing field `y`')
case('an unknown field is an Err', DECL + 'println(read[Point]("Point(x: 1, z: 2)"))' + '\n', 0, '`z` is not a field')
case('a repeated field is an Err', DECL + 'println(read[Point]("Point(x: 1, y: 2, x: 3)"))' + '\n', 0, 'field `x` is given twice')
case('a wrong scalar is an Err', DECL + 'println(read[Point]("Point(x: 1, y: abc)"))' + '\n', 0, 'field `y`')
case('a nested tuple reads', DECL + 'println(read[Order]("Order(customer: Customer(name: \\"Ann\\", vip: true), total: 30)"))' + '\n', 0, 'Ok(Order(customer: Customer(name: "Ann", vip: true), total: 30))')
case('a nested missing field names its path', DECL + 'println(read[Order]("Order(customer: Customer(name: \\"Ann\\"), total: 30)"))' + '\n', 0, 'field `customer`: missing field `vip`')
case('a nested wrong type names its path', DECL + 'println(read[Order]("Order(customer: Customer(name: \\"Ann\\", vip: 3), total: 30)"))' + '\n', 0, 'field `customer`: field `vip`')

ENUMS = 'enum Shape deriving show, read\n  Circle(r Float),\n  Rect(w Int, h Int),\n  Dot\ntuple Scene deriving read, show\n  shapes List[Shape]\n'

case('an enum unit case reads', ENUMS + 'println(read[Shape]("Dot"))' + '\n', 0, 'Ok(Shape.Dot)')
case('a qualified case reads', ENUMS + 'println(read[Shape]("Shape.Dot"))' + '\n', 0, 'Ok(Shape.Dot)')
case('a case with fields reads', ENUMS + 'println(read[Shape]("Circle(r: 1.5)"))' + '\n', 0, 'Ok(Shape.Circle(1.5))')
case('a case missing a field is an Err', ENUMS + 'println(read[Shape]("Rect(w: 2)"))' + '\n', 0, 'missing field `h`')
case('an unknown case is an Err', ENUMS + 'println(read[Shape]("Tri"))' + '\n', 0, 'is not a case of Shape')
case('a List reads', ENUMS + 'println(read[List[Int]]("List(1, 2, 3)"))' + '\n', 0, 'Ok(List(1, 2, 3))')
case('a bad List item names its index', ENUMS + 'println(read[List[Int]]("List(1, b)"))' + '\n', 0, 'item 1')
case('a List of enums inside a tuple reads', ENUMS + 'println(read[Scene]("Scene(shapes: List(Dot, Rect(1, 2)))"))' + '\n', 0, 'Ok(Scene(shapes: List(Shape.Dot, Shape.Rect(1, 2))))')
case('show then read round-trips', ENUMS + 'x = Scene(shapes: List(Dot, Circle(r: 2.0)))\nprintln(read[Scene](show(x)) == Ok(x))' + '\n', 0, 'true')
case('read of an enum without deriving read is a compile error', 'enum Plain deriving show\n  A,\n  B\nprintln(read[Plain]("A"))\n', 2, "doesn't implement `Read`")

H = 'enum Level(code Int, label String) deriving read\n  Low(1, "low")\n  High(9, "high")\ntuple Conf deriving read\n  names Set[String]\n  limits Dict[String, Int]\n  level Level\n'
case('a Dict, a Set and a header enum read', H + 'println(read[Conf]("Conf(names: Set(\\"a\\", \\"b\\"), limits: Dict(\\"x\\" -> 1, \\"y\\" -> 2), level: Level.High(9, \\"high\\"))"))' + '\n', 0, 'Ok(Conf(names: Set("a", "b"), limits: Dict("x" -> 1, "y" -> 2), level: Level.High(9, "high")))')
case('a header case reads by its bare name', H + 'println(read[Level]("Low"))' + '\n', 0, 'Ok(Level.Low(1, "low"))')
case('a header case with other values is an Err', H + 'println(read[Level]("Level.Low(5, \\"low\\")"))' + '\n', 0, 'not `Level.Low(5,')
case('a bad Dict value names its entry', H + 'println(read[Conf]("Conf(names: Set(), limits: Dict(\\"x\\" -> \\"no\\"), level: Low)"))' + '\n', 0, 'field `limits`: entry 0')
case('a Dict entry needs an arrow', H + 'println(read[Dict[String, Int]]("Dict(\\"x\\" 1)"))' + '\n', 0, 'expected `key -> value`')
case('a colon inside a key is part of the key', H + 'println(read[Dict[String, Int]]("Dict(\\"k:v\\" -> 3)"))' + '\n', 0, 'Ok(Dict("k:v" -> 3))')
case('a bad Set item names its index', H + 'println(read[Set[Int]]("Set(1, x)"))' + '\n', 0, 'item 1')
case('show then read round-trips a Dict and a Set', H + 'c = Conf(names: Set("n"), limits: Dict("a" -> 1), level: Level.Low)\nprintln(read[Conf](show(c)) == Ok(c))' + '\n', 0, 'true')

print(f"{len(fails)} failed" if fails else "all passed")
sys.exit(1 if fails else 0)
