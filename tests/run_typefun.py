"""Type functions: `type alias F[T] = when T: pattern -> type`, matching, recursion, numbers, fuel.  Run: python3 tests/run_typefun.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ELEM = 'type alias Elem[T] = when T\n  List[X] -> X\n  Array[X][N] -> X\n'
CONCAT = 'type alias Concat[A, B] = when A\n  () -> B\n  (H, ...T) -> (H, ...Concat[T, B])\n'
LENGTH = 'type alias Length[T] = when T\n  () -> 0\n  (H, ...Rest) -> 1 + Length[Rest]\n'
SHRINK = 'type alias Shrink[T] = when T\n  Array[X][N] -> Array[X][N - 1]\n'
BOX = 'tuple Box[T]\n  v T\n'
BAD = [
 ("Elem of a List", ELEM + 'a Elem[List[String]] = 3\n', "expected `String`, found `Int`"),
 ("Elem of an Array", ELEM + 'a Elem[Array[Int][3]] = "s"\n', "expected `Int`, found `String`"),
 ("no arm matches", ELEM + BOX + 'a Elem[Box[Int]] = 3\n', "no arm of `Elem` matches `Box[Int]`"),
 ("Concat joins tuple types", CONCAT + 'd Concat[(Int, String), (Bool,)] = (1, "a", 2)\n', "expected `(Int, String, Bool)`, found `(Int, String, Int)`"),
 ("Length gives a size", LENGTH + 'b Array[Int][Length[(Int, String, Bool)]] = Array(1, 2)\n', "expected `Array[Int][3]`, found `Array[Int][2]`"),
 ("size arithmetic in a result", SHRINK + 'd Shrink[Array[Int][3]] = Array(1, 2, 3)\n', "expected `Array[Int][2]`, found `Array[Int][3]`"),
 ("a stuck type is only itself", ELEM + 'fn f[C](x C) Elem[C]\n  x\n', "expected `Elem[C]`, found `C`"),
 ("a type function in a result type", ELEM + 'fn f(xs List[Int]) Elem[List[Int]]\n  "s"\n', "expected `Int`, found `String`"),
 ("the fuel stops a runaway", 'type alias Spin[T] = when T\n  X -> Spin[(X, X)]\ns Spin[Int] = 1\n', "grew past the size limit"),
 ("the fuel stops a slow one", 'type alias Count[T] = when T\n  X -> Count[Array[X][1]]\ns Count[Int] = 1\n', "did not finish in 64 reductions"),
 ("an arm that does not shrink is warned about", 'type alias Spin[T] = when T\n  X -> Spin[(X, X)]\n', "which is not a piece of what its arm matched"),
]
GOOD = [
 ("Elem of a List", ELEM + 'a Elem[List[String]] = "s"\nprintln(a)\n', "s"),
 ("Elem in a result type", ELEM + 'fn head_of(xs Array[Int][3]) Elem[Array[Int][3]]\n  xs(0)\nprintln(head_of(Array(7, 8, 9)))\n', "7"),
 ("Concat of tuple types", CONCAT + 'e Concat[(Int, String), (Bool,)] = (1, "a", true)\nprintln(e)\n', "1"),
 ("Concat in a generic function", CONCAT + 'fn pair_up[T](x T) Concat[(T,), (Int,)]\n  (x, 0)\nprintln(pair_up("a"))\n', "a"),
 ("Length as a size", LENGTH + 'b Array[Int][Length[(Int, String)]] = Array(1, 2)\nprintln(b(1))\n', "2"),
 ("size arithmetic", SHRINK + 'c Shrink[Array[Int][3]] = Array(1, 2)\nprintln(c(1))\n', "2"),
 ("an arm that shrinks gets no warning", LENGTH + 'println("ok")\n', "ok"),
]
PAD = 'type alias Pad[N] = when N\n  M if M > 3 -> Array[Int][M]\n  M if M <= 3 -> Array[Int][3]\n'
COL = 'type alias Col[K] = when K\n  "id" -> Int\n  "name" -> String\n'
SAME = 'type alias Same[A, B] = when A\n  X if X == B -> Bool\n  X -> Unit\n'
BAD += [
 ("a guard picks the arm: big", PAD + 'c Pad[5] = Array(1, 2)\n', "expected `Array[Int][5]`, found `Array[Int][2]`"),
 ("a guard picks the arm: small", PAD + 'c Pad[2] = Array(1, 2)\n', "expected `Array[Int][3]`, found `Array[Int][2]`"),
 ("a string as a type", COL + 'd Col["id"] = "x"\n', "expected `Int`, found `String`"),
 ("no string arm", COL + 'f Col["zip"] = 1\n', "no arm of `Col` matches `\"zip\"`"),
 ("== in a guard compares types", SAME + 'g Same[Int, String] = true\n', "expected `Unit`, found `Bool`"),
 ("a guard that is not a comparison", 'type alias T[N] = when N\n  M if M -> Int\n  M -> Unit\nx T[1] = 1\n', "a guard in a type function compares"),
]
GOOD += [
 ("guards: the large arm", PAD + 'a Pad[5] = Array(1, 2, 3, 4, 5)\nprintln(a(4))\n', "5"),
 ("guards: the small arm", PAD + 'b Pad[2] = Array(1, 2, 3)\nprintln(b(2))\n', "3"),
 ("a string arm", COL + 'e Col["name"] = "x"\nprintln(e)\n', "x"),
 ("== in a guard: equal types", SAME + 'g Same[Int, Int] = true\nprintln(g)\n', "true"),
]
GET = 'type alias Get[R, K] = when R\n  (K T, ...Rest) -> T\n  (_ _, ...Rest) -> Get[Rest, K]\nfn get[R, K](row R, key K) Get[R, K]\n  todo\n'
NAMES = 'type alias Names[R] = when R\n  () -> ()\n  (k _, ...Rest) -> (k, ...Names[Rest])\n'
USER = 'tuple User\n  id Int\n  name String\n  zip Int\n'
BAD += [
 ("get finds a field by name: wrong type", GET + USER + 'u = User(id: 1, name: "a", zip: 3)\nx Int = get(u, "name")\n', "expected `Int`, found `String`"),
 ("get: no such field", GET + USER + 'u = User(id: 1, name: "a", zip: 3)\nz = get(u, "nope")\n', "no arm of `Get` matches"),
 ("labels are shown", GET + 'x Get[(a Int, b String), "b"] = 1\n', "expected `String`, found `Int`"),
 ("field names as strings", NAMES + 'x Names[(a Int, b String)] = (1, 2)\n', "expected `(\"a\", \"b\")`"),
]
GOOD += [
 ("get finds a field by name", GET + USER + 'fn look(u User) Unit\n  y String = get(u, "name")\n  z Int = get(u, "zip")\n  println(y)\nprintln("ok")\n', "ok"),
]
NAMED = 'interface Named\n  fn name() String\ntuple Dog\n  n String\nimpl Named for Dog\n  fn name() String = n\ntype alias Label[T] = when T\n  X Named -> String\n  _ -> Int\n'
BAD += [
 ("X: Iface matches an implementer", NAMED + 'c Label[Dog] = 3\n', "expected `String`, found `Int`"),
 ("X: Iface skips a non-implementer", NAMED + 'd Label[Bool] = "s"\n', "expected `Int`, found `String`"),
]
GOOD += [
 ("X: Iface picks the arm", NAMED + 'a Label[Dog] = "x"\nb Label[Bool] = 3\nprintln(a)\n', "x"),
]
CONT = 'interface Container\n  type Item\n  fn first() Item\ntuple Names\n  xs List[String]\nimpl Container for Names\n  type Item = String\n  fn first() String = xs(0)\nfn head[C Container](c C) C.Item\n  c.first()\n'
BAD += [
 ("a concrete associated type", CONT + 'b Names.Item = 3\n', "expected `String`, found `Int`"),
 ("an associated type from a call", CONT + 'a Int = head(Names(xs: List("a")))\n', "expected `Int`, found `String`"),
 ("an associated type in a generic body", CONT + 'fn bad[C Container](c C) C.Item\n  "s"\n', "expected `C.Item`, found `String`"),
]
GOOD += [
 ("an associated type from a call is right", CONT + 'a String = head(Names(xs: List("a")))\nprintln(a)\n', "a"),
]
ANY = 'interface Container\n  type Item\n  fn first() Item\n  fn put(x Item) Unit\n'
BAD += [
 ("one any value's Item is not another's", ANY + 'fn mv(from any Container, to any Container) Unit\n  to.put(from.first())\n', "expected `to.Item`, found `from.Item`"),
 ("a tail call on the wrong any", ANY + 'fn mix(a any Container, b any Container) a.Item\n  b.first()\n', "expected `a.Item`, found `b.Item`"),
 ("a result tied to the argument", ANY + 'fn first_of(c any Container) c.Item\n  c.first()\nfn use(a any Container, b any Container) Unit\n  b.put(first_of(a))\n', "expected `b.Item`, found `a.Item`"),
 ("x.Item of a concrete parameter", CONT + 'fn f(n Names) n.Item\n  return 3\n', "expected `String`, found `Int`"),
]
GOOD += [
 ("the same any value agrees with itself", ANY + 'fn copy_first(c any Container) Unit\n  c.put(c.first())\nfn first_of(c any Container) c.Item\n  c.first()\nfn twice(a any Container) Unit\n  a.put(first_of(a))\nprintln("ok")\n', "ok"),
]
MK = 'fn make() any Container\n  todo\n'
BAD += [
 ("an any local has its own Item", ANY + MK + 'fn f(a any Container) Unit\n  x any Container = make()\n  x.put(a.first())\n', "expected `x.Item`, found `a.Item`"),
 ("an alias of an any local shares its Item", ANY + MK + 'fn f(a any Container) Unit\n  x any Container = make()\n  z = x\n  a.put(z.first())\n', "expected `a.Item`, found `x.Item`"),
]
GOOD += [
 ("an any local agrees with itself and its alias", ANY + MK + 'fn f(a any Container) Unit\n  x any Container = make()\n  x.put(x.first())\n  y = a\n  y.put(a.first())\nprintln("ok")\n', "ok"),
]
BIG = 'fn big(n Int) Bool\n  n > 3\ntype alias Pad2[N] = when N\n  M if big(M) -> Array[Int][M]\n  M -> Array[Int][3]\n'
BAD += [
 ("a guard that calls a function: true", BIG + 'a Pad2[5] = Array(1, 2)\n', "expected `Array[Int][5]`, found `Array[Int][2]`"),
 ("a guard that calls a function: false", BIG + 'b Pad2[2] = Array(1, 2)\n', "expected `Array[Int][3]`, found `Array[Int][2]`"),
 ("the first use is named when no arm matches", GET + USER + 'z = get(User(id: 1, name: "a", zip: 3), "nope")\n', "(while working out `Get[User, \"nope\"]`)"),
 ("a constant that is always an Err is warned about", 'fn port(n Int) Result[Int, String]\n  if n > 65535 then fail(1, "too big") else Ok(n)\np = port(99999)\nprintln(p)\n', "always gives `Err("),
]
GOOD += [
 ("a guard that calls a function picks the arm", BIG + 'a Pad2[5] = Array(1, 2, 3, 4, 5)\nb Pad2[2] = Array(1, 2, 3)\nprintln(a(4))\n', "5"),
]
NA = 'interface Named\n  fn name() String\ninterface Aged\n  fn age() Int\ntuple Dog\n  n String\ntuple Cat\n  n String\n  a Int\nimpl Named for Dog\n  fn name() String = n\nimpl Named for Cat\n  fn name() String = n\nimpl Aged for Cat\n  fn age() Int = a\n'
DESC = 'fn describe(x any Named + Aged) String\n  "${x.name()} ${x.age()}"\n'
BAD += [
 ("an intersection needs every interface", NA + DESC + 'println(describe(Dog(n: "rex")))\n', "`Dog` doesn't implement `Aged`, which `any Named + Aged` needs for `x`"),
 ("a single any is checked too", NA + 'fn f(x any Aged) Int\n  x.age()\nprintln(f(Dog(n: "r")))\n', "`Dog` doesn't implement `Aged`"),
 ("X: A + B matches only both", NA + 'type alias Kind[T] = when T\n  X Named + Aged -> String\n  _ -> Int\nb Kind[Dog] = "s"\n', "expected `Int`, found `String`"),
]
GOOD += [
 ("an intersection takes a type with both", NA + DESC + 'println(describe(Cat(n: "tom", a: 3)))\n', "tom 3"),
 ("X: A + B matches a type with both", NA + 'type alias Kind[T] = when T\n  X Named + Aged -> String\n  _ -> Int\na Kind[Cat] = "s"\nprintln(a)\n', "s"),
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
# the reduction limit comes from [program] type_fuel in Moxie.toml
import shutil
d = tempfile.mkdtemp()
open(os.path.join(d, "main.mxi"), "w").write(LENGTH + 'a Array[Int][Length[(Int, Int, Int, Int, Int, Int)]] = Array(1, 2, 3, 4, 5, 6)\nprintln("ok")\n')
for fuel, want in ((None, True), (4, False), (50, True)):
    open(os.path.join(d, "Moxie.toml"), "w").write("[program]\n" + (f"type_fuel = {fuel}\n" if fuel else ""))
    r = subprocess.run([sys.executable, "-m", "moxie", "check", os.path.join(d, "main.mxi")], cwd=ROOT, capture_output=True, timeout=60)
    o = r.stdout.decode() + r.stderr.decode()
    ok = (r.returncode == 0) if want else ("did not finish in 4 reductions" in o)
    print(("ok    " if ok else "FAIL  ") + f"type_fuel = {fuel}" + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(f"fuel {fuel}")
open(os.path.join(d, "Moxie.toml"), "w").write("[program]\ntype_fuel = 0\n")
r = subprocess.run([sys.executable, "-m", "moxie", "check", os.path.join(d, "main.mxi")], cwd=ROOT, capture_output=True, timeout=60)
o = r.stdout.decode() + r.stderr.decode()
ok = r.returncode != 0 and "type_fuel must be a whole number" in o
print(("ok    " if ok else "FAIL  ") + "type_fuel must be 1 or more" + ("" if ok else f"  {o[:300]!r}"))
if not ok:
    fails.append("fuel 0")
shutil.rmtree(d, ignore_errors=True)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
