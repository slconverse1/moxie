"""Mistakes the checker must report, and valid programs it must accept.  Run: python3 tests/run_audit.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check(src, flags=()):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", *flags, "check", f.name], cwd=ROOT, capture_output=True, timeout=60)
        out = (r.stdout + r.stderr).decode()
    except subprocess.TimeoutExpired:
        out = "TIMEOUT"
    os.unlink(f.name)
    return out

P = '\ntuple User deriving show:\n  name: String\n  age: Int\nenum Shape:\n  Circle(r: Int)\n  Sq(s: Int)\n'

BAD = [
 ('interpolate a stream', 'xs = List(1, 2)\ns = xs |> filter(_ > 1)\nprintln("${s}")\n'),
 ('println a stream', 'xs = List(1, 2)\nprintln(xs |> map(_ + 1))\n'),
 ('pipe a stream to println', 'xs = List(1, 2)\nxs |> map(_ + 1) |> println()\n'),
    ("bare field in self method", "tuple A:\n  owner: String\nimpl A:\n  fn name(self) String:\n    owner\n"),
 ('wrong arg type to user fn', 'fn f(n: Int) Int:\n  n\nx = f("a")\n'),
 ('too many args', 'fn f(n: Int) Int:\n  n\nx = f(1, 2)\n'),
 ('too few args', 'fn f(n: Int, m: Int) Int:\n  n\nx = f(1)\n'),
 ('wrong return', 'fn f(n: Int) String:\n  n\n'),
 ('return stmt wrong type', 'fn f(n: Int) String:\n  return n\n'),
 ('if branches differ as tail', 'fn f(n: Int) Int:\n  if n > 0:\n    1\n  else:\n    "x"\n'),
 ('missing field in ctor', P + 'u = User(name: "a")\n'),
 ('wrong field type in ctor', P + 'u = User(name: 1, age: 2)\n'),
 ('unknown field access', P + 'u = User(name: "a", age: 1)\nprintln(u.nme)\n'),
 ('field type misuse', P + 'u = User(name: "a", age: 1)\nx: String = u.age\n'),
 ('non-exhaustive when', P + 'fn f(s: Shape) Int:\n  when s:\n    Circle(r) -> r\n'),
 ('unknown enum case', P + 'x = Shape.Tri(1)\n'),
 ('enum payload wrong type', P + 'x = Shape.Circle("a")\n'),
 ('Int + String', 'x = 1 + "a"\n'),
 ('String * String', 'x = "a" * "b"\n'),
 ('Bool arithmetic', 'x = true + 1\n'),
 ('compare Int to String', 'x = 1 == "a"\n'),
 ('if cond Int', 'if 1:\n  println(1)\n'),
 ('while cond String', 'while "a":\n  println(1)\n'),
 ('not on Int', 'x = not 5\n'),
 ('undefined name', 'println(nope)\n'),
 ('undefined fn', 'x = nope(1)\n'),
 ('annotation mismatch', 'x: Int = "a"\n'),
 ('list elem mismatch', 'x = List(1, "a")\n'),
 ('list annotation mismatch', 'x: List[Int] = List("a")\n'),
 ('dict value mismatch', 'x: Dict[String, Int] = Dict("a": "b")\n'),
 ('set elem mismatch', 'x: Set[Int] = Set("a")\n'),
 ('Result wrong ok type', 'fn f() Result[Int, Error]:\n  Ok("a")\n'),
 ('Result returns bare value', 'fn f() Result[Int, Error]:\n  1\n'),
 ('Err wrong type', 'fn f() Result[Int, String]:\n  Err(5)\n'),
 ('? on non-Result', 'fn f() Result[Int, Error]:\n  x = 5?\n  Ok(x)\n'),
 ('? error type mismatch', 'fn g() Result[Int, String]:\n  Ok(1)\nfn f() Result[Int, Int]:\n  x = g()?\n  Ok(x)\n'),
 ('map_err wrong fn', 'r: Result[Int, String] = Ok(1)\nx = r.map_err(5)\n'),
 ('unwrap non result', 'x = 5.get_or(1)\n'),
 ('println too many', 'println(1, 2, 3)\n'),
 ('len of Int', 'x = len(5)\n'),
 ('upper of Int', 'x = upper(5)\n'),
 ('trim of List', 'x = trim(List(1))\n'),
 ('sqrt of String', 'x = sqrt("a")\n'),
 ('abs of String', 'x = abs("a")\n'),
 ('max mixed', 'x = max(1, "a")\n'),
 ('sum of Bools', 'x = List(true) |> sum()\n'),
 ('map wrong arity lambda', 'x = List(1, 2).map((a, b): a) |> collect()\n'),
 ('filter non-bool', 'x = List(1, 2).filter((a): a + 1) |> collect()\n'),
 ('reduce wrong init', 'x = List(1, 2) |> reduce("a", (acc, n): acc + n)\n'),
 ('map result misuse', 'x: List[String] = List(1, 2).map((a): a + 1) |> collect()\n'),
 ('index with String', 'xs = List(1, 2)\nx = xs("a")\n'),
 ('index non-indexable', 'x = 5\ny = x(0)\n'),
 ('List index result misuse', 'xs = List(1, 2)\ny: String = xs(0)\n'),
 ('dict key type', 'd: Dict[String, Int] = Dict("a": 1)\nx = d(5)\n'),
 ('push wrong elem', 'xs: List[Int] = List(1)\nys = push(xs, "a")\n'),
 ('channel write wrong type', 'rx, tx = Chan[Int][1]()\n\\write(tx, "a")\n'),
 ('channel read from write end', 'rx, tx = Chan[Int][1]()\nx = read(tx)\n'),
 ('write to read end', 'rx, tx = Chan[Int][1]()\n\\write(rx, 1)\n'),
 ('future resolve wrong', 'r, w = Future[Int]()\nresolve(w, "a")\n'),
 ('spawn non-fn', 'x = spawn(5)\n'),
 ('use after move', 'rx, tx = Chan[Int][1]()\nchan2 = move rx\nx = read(rx)\n'),
 ('resource not moved into tuple', 'tuple H:\n  c: ChanW[Int]\nrx, tx = Chan[Int][1]()\nh = H(c: tx)\n'),
 ('wrong lambda return in higher-order', 'fn ap(f: (Int) -> Int, x: Int) Int:\n  f(x)\nx = ap((n): "a", 1)\n'),
 ('fn value wrong type', 'fn s(n: Int) String:\n  "a"\nfn ap(f: (Int) -> Int, x: Int) Int:\n  f(x)\nx = ap(s, 1)\n'),
 ('generic fn two types', 'fn same[T](a: T, b: T) T:\n  a\nx = same(1, "a")\n'),
 ('generic bound violated', 'fn big[T: Ordered](a: T, b: T) T:\n  a\nx = big(User(name: "a", age: 1), User(name: "b", age: 2))\n'),
 ('interface missing impl', 'interface Named:\n  fn name(self) String\nfn show_name[T: Named](x: T) String:\n  x.name()\nx = show_name(5)\n'),
 ('method on wrong type', 'x = 5.upper()\n'),
 ('call non-function', 'x = 5\ny = x()\n'),
 ('Unit fn value used', 'fn f() Unit:\n  println(1)\nx: Int = f()\n'),
 ('tuple destructure arity', 'a, b, c = (1, 2)\n'),
 ('tuple index out of range', 't = (1, 2)\nx = t(5)\n'),
 ('duplicate field', 'tuple T:\n  a: Int\n  a: Int\n'),
 ('wrong type arity', 'x: List[Int, Int] = List(1)\n'),
 ('unknown type', 'x: Nope = 1\n'),
 ('Option misuse', 'x: Maybe[Int] = Just(1)\n'),
 ('range of strings', 'for i in "a".."c":\n  println(i)\n'),
 ('for over Int', 'for i in 5:\n  println(i)\n'),
 ('Dict iteration pattern', 'd: Dict[String, Int] = Dict("a": 1)\nfor k in d:\n  y: Int = k\n'),
 ('string compare ops', 'x = "a" - "b"\n'),
 ('float modulo string', 'x = 1.5 % "a"\n'),
 ('neg of string', 'x = -"a"\n'),
 ('Duration add Int', 'x = 5s + 1\n'),
 ('Int to Float fn', 'fn f(x: Float) Float:\n  x\ny = f("a")\n'),
 ('pipe wrong type', 'fn f(s: String) Int:\n  len(s)\nx = 5 |> f()\n'),
 ('UFCS wrong type', 'fn f(s: String) Int:\n  len(s)\nx = 5.f()\n'),
 ('sort non-ordered', 'x = List(User(name: "a", age: 1)).sort()\n'),
 ('contains wrong type', 'x = List(1, 2).contains("a")\n'),
 ('split on Int', 'x = split(5, ",")\n'),
 ('parse wrong', 'x: Int = parse_int(5)\n'),
 ('regex arg', 'x = matches(5, "a")\n'),
 ('File read misuse', 'x = read_file(5)\n'),
 ('println of result then arithmetic', 'r: Result[Int, Error] = Ok(1)\nx = r + 1\n'),
 ('when arm types differ', 'x = when 1:\n  1 -> "a"\n  _ -> 2\n'),
 ('select on non-chan', 'select:\n  case 5 -> println(1)\n'),
 ('atom swap wrong type', 'a = Atom[Int](0)\nswap(a, "x")\n'),
 ('atom init wrong', 'a: Atom[Int] = Atom[Int]("a")\n'),
 ("if without else gives a value", "x = if true:\n  1\n"),
 ("interpolating a function", "fn g() Int:\n  1\nprintln(\"${g}\")\n"),
 ("unreachable second clause", "fn f() Int:\n  1\nfn f() Int:\n  2\n"),
]

GOOD = [
 '// stats and matrices\ntuple Summary deriving show:\n  count: Int\n  mean: Float\n  top: Int\n\nreadings: MultiArray[Int][3, 4] = (\n  4, 8, 15, 16 ;\n  23, 42, 7, 9 ;\n  1, 2, 3, 5\n)\n\nfn row_total[R, C](g: MultiArray[Int][R, C], r: Int) Int:\n  g(r, ..) |> to_stream() |> reduce(0, _1 + _2)\n\nfn col_max[R, C](g: MultiArray[Int][R, C], c: Int) Int:\n  g(.., c) |> to_stream() |> reduce(0, max(_1, _2))\n\nfn summarize(xs: List[Int]) Result[Summary, Error]:\n  m = avg(xs)?\n  Ok(Summary(count: len(xs), mean: m, top: xs |> reduce(0, max(_1, _2))))\n\ntotals = List(row_total(readings, 0), row_total(readings, 1), row_total(readings, 2))\nprintln("${totals} ${sum(totals)}")\nprintln("${col_max(readings, 1)} ${readings(1, 1)}")\nwhen summarize(totals):\n  Ok(s) -> println("${s}")\n  Err(e) -> println("err ${e.message}")\nwhen summarize(List()):\n  Ok(s) -> println("${s}")\n  Err(e) -> println("empty")\nevens = totals |> filter(_ % 2 == 0) |> map(_ * 2) |> collect()\nprintln("${evens} ${product(List(1, 2, 3, 4))} ${avg(List(1.5, 2.5))}")\nsquares = (1..=5) |> to_stream() |> map(_ * _) |> collect()\nprintln("${squares}")\n',
 '// accounts: tuples, impl, interface, generics, typed errors with From\nenum BankError deriving show:\n  NoFunds(needed: Int),\n  Frozen,\n  Parse(msg: String)\n\ntuple Account deriving show:\n  id: Int\n  owner: String\n  balance: Int = 0\n  frozen: Bool = false\n\ninterface Describe:\n  fn describe(self) String\n\nimpl Describe for Account:\n  fn describe(self) String:\n    "#${self.id} ${self.owner}: ${self.balance}"\n\nimpl Account:\n  fn deposit(self, amount: Int) Account:\n    Account(id: self.id, owner: self.owner, balance: self.balance + amount, frozen: self.frozen)\n  fn withdraw(self, amount: Int) Result[Account, BankError]:\n    if self.frozen:\n      return Err(BankError.Frozen)\n    if amount > self.balance:\n      return Err(BankError.NoFunds(needed: amount - self.balance))\n    Ok(Account(id: self.id, owner: self.owner, balance: self.balance - amount, frozen: self.frozen))\n\nfn parse_amount(text: String) Result[Int, BankError]:\n  when read[Int](text):\n    Ok(n) -> Ok(n)\n    Err(e) -> Err(BankError.Parse(msg: "bad amount: ${text}"))\n\nfn transfer(from: Account, to: Account, text: String) Result[(Account, Account), BankError]:\n  amount = parse_amount(text)?\n  a = from.withdraw(amount)?\n  Ok((a, to.deposit(amount)))\n\nfn show_all[T: Describe](xs: List[T]) Unit:\n  for x in xs:\n    println(x.describe())\n\nalice = Account(id: 1, owner: "alice", balance: 100)\nbob = Account(id: 2, owner: "bob")\nshow_all(List(alice, bob))\nwhen transfer(alice, bob, "30"):\n  Ok((a, b)) -> show_all(List(a, b))\n  Err(e) -> println("failed: ${e}")\nwhen transfer(alice, bob, "300"):\n  Ok(_) -> println("?")\n  Err(e) -> println("failed: ${e}")\nwhen transfer(alice, bob, "x"):\n  Ok(_) -> println("?")\n  Err(e) -> println("failed: ${e}")\n',
 "fn fib(0) Int:\n  0\nfn fib(1) Int:\n  1\nfn fib(n: Int) Int:\n  fib(n - 1) + fib(n - 2)\nprintln(fib(10))\nif true:\n  println(1)\nx = if true: 1 else: 2\n",
 "fn server(tx: ChanW[Int]) Unit:\n  l = listen(0)?\n  \\write(tx, port_of(l))\n",
 "enum Planet:\n  EARTH\n  MARS\nx = Planet.values()\ny = Planet.value_of(\"EARTH\")\n",
 "x = if true: 1 else: 2.5\ny = if true: 1 else: 2\nz = when 3:\n  1 -> \"a\"\n  _ -> \"b\"\n",
 "d: Dict[String, Int] = Dict(\"a\": 1)\nfor (k, v) in d:\n  println(\"${k}${v + 1}\")\n",
 "tuple User:\n  name: String\n  age: Int = 0\nu = User(name: \"a\")\nv = User(\"a\", 3)\n",
 "fn g() Result[Int, String]:\n  Ok(1)\nfn f() Result[Int, String]:\n  x = g()?\n  Ok(x)\n",
 "x = -5\ny = -(2 + 3)\nz = -1.5\nfor i in 1..3:\n  println(i)\n",
 "xs = List(1, 2)\nprintln(xs(0) + xs(1))\nt = (1, \"a\")\nprintln(t(0))\n",
 "fn f(s: String) Int:\n  len(s)\nprintln(\"abc\" |> f())\nprintln(\"abc\".f())\n",
]

fails = []
for name, src in BAD:
    out = check(src)
    ok = "error" in out and "syntax error" not in out and "Traceback" not in out
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {out.strip()[:160]!r}"))
    if not ok:
        fails.append(name)
for i, src in enumerate(GOOD):
    for flags in ((), ("--gc",)):
        out = check(src, flags)
        ok = out.strip().endswith(": ok")
        print(("ok    " if ok else "FAIL  ") + f"valid program {i + 1}" + (" (gc)" if flags else "") + ("" if ok else f"  {out.strip()[:200]!r}"))
        if not ok:
            fails.append(f"good {i + 1}")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
