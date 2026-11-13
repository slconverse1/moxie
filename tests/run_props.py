"""Properties: accessors, field, computed, lazy, static, interface members, observers.  Run: python3 tests/run_props.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ACCT = '''tuple Account
  owner String,
  property balance Int = 0
    priv set(value)
      assert(value >= 0)
      field = value
    did_set(old)
      println("changed ${old} -> ${balance}")
impl Account
  fn (ref Self) deposit(n Int) Unit
    balance = balance + n
'''

# (name, source, how, text): how is "run" (exit 0 and text in output), "fail" (nonzero exit and text in output)
CASES = [
 ("an observer handler with one parameter is a compile error",
  'tuple Meter\n  property level Int = 0\nm = Atom(Meter())\ntok = on_change(m, level, fn (a) -> println(a))\n', "fail", "takes two parameters"),
 ("an observer handler typed for another type is a compile error",
  'tuple Meter\n  property level Int = 0\nm = Atom(Meter())\nm.level +% fn (a String, b String) -> println(a)\n', "fail", "expected `Int`, found `String`"),
 ("an observer handler of the right shape is accepted",
  'tuple Meter\n  property level Int = 0\nm = Atom(Meter())\ntok = on_change(m, level, fn (a, b) -> println("$a $b"))\nprintln("ok")\n', "run", "ok"),
 ("a stored property with no accessors reads and writes",
  'tuple T\n  property n Int = 3\nt = T()\nprintln(t.n)\nt.n = 9\nprintln(t.n)\n', "run", "3\n9"),
 ("a setter validates a write",
  ACCT + 'a = Account(owner: "Ann", balance: 5)\na.deposit(1)\nprintln(a.balance)\na.deposit(0 - 50)\n', "fail", "assertion failed"),
 ("a setter runs at construction",
  ACCT + 'a = Account(owner: "Ann", balance: -1)\n', "fail", "assertion failed"),
 ("did_set runs on a change inside the type, not at construction, not for the same value",
  ACCT + 'a = Account(owner: "Ann", balance: 5)\nprintln("built")\na.deposit(0)\na.deposit(2)\nprintln(a.balance)\n', "run", "built\nchanged 5 -> 7\n7"),
 ("a computed property stores nothing",
  'tuple Rect\n  width Int,\n  height Int,\n  property area Int\n    get\n      width * height\nr = Rect(width: 3, height: 4)\nprintln(r.area)\nprintln(r)\n', "run", "12\nRect(width: 3, height: 4)"),
 ("a computed property may have a setter that writes other fields",
  'tuple Rect\n  width Int,\n  height Int,\n  property area Int\n    get\n      width * height\n    set(v)\n      width = v / height\nr = Rect(width: 3, height: 4)\nr.area = 24\nprintln("${r.width} ${r.area}")\n', "run", "6 24"),
 ("a one-line get",
  'tuple R\n  w Int,\n  property twice Int\n    get -> w * 2\nprintln(R(w: 4).twice)\n', "run", "8"),
 ("a lazy property is recomputed for a rebuilt value",
  'tuple R\n  data List[Int],\n  lazy property total Int\n    get\n      data |> to_stream() |> sum()\nr = R(data: List(1, 2, 3))\nprintln("${r.total} ${r.total}")\nr.data = List(10, 20)\nprintln(r.total)\n', "run", "6 6\n30"),
 ("a lazy property must be pure",
  'tuple R\n  w Int,\n  lazy property t Int\n    get\n      println("hi")\n      w\nprintln(1)\n', "fail", "prints"),
 ("a static property is read through the type",
  'tuple Account\n  owner String\n  static property rate Float = 0.05\n  static property bank String\n    get -> "First"\nprintln("${Account.rate} ${Account.bank}")\n', "run", "0.05 First"),
 ("a static property is read-only",
  'tuple A\n  owner String\n  static property rate Float = 0.05\nA.rate = 0.1\n', "fail", "read-only"),
 ("a property without a setter is read-only",
  'tuple R\n  w Int,\n  property twice Int\n    get -> w * 2\nr = R(w: 2)\nr.twice = 5\n', "fail", "read-only"),
 ("priv set can't be used outside the type",
  ACCT + 'a = Account(owner: "Ann")\na.balance = 5\n', "fail", "private"),
 ("an interface can require a property that a property satisfies",
  'interface Named\n  name String\ninterface Wallet\n  property balance Int\ntuple P\n  given String,\n  property name String\n    get -> given\ntuple W\n  property balance Int = 4\nimpl Named for P\nimpl Wallet for W\nfn hi[T Named](x T) String\n  "Hello, ${x.name}"\nprintln(hi(P(given: "Ada")))\n', "run", "Hello, Ada"),
 ("an impl that lacks a required property is an error",
  'interface Named\n  name String\ntuple B\n  id Int\nimpl Named for B\nprintln(1)\n', "fail", "has no field or property `name`"),
 ("an interface that asks for set rejects a read-only property",
  'interface Wallet\n  property balance Int\ntuple W\n  w Int,\n  property balance Int\n    get -> w\nimpl Wallet for W\nprintln(1)\n', "fail", "read-only"),
 ("observers hear a change once and can be removed",
  'tuple Account\n  owner String,\n  property balance Int = 0\nfn save_row(old Int, new Int) Unit\n  println("db ${old} -> ${new}")\nshared = Atom[Account](Account(owner: "Ann"))\ndb = shared.balance +% save_row\nui = shared.on_change(balance, fn (o, n) -> println("ui ${n}"))\n\\swap(shared, (a) -> Account(owner: a.owner, balance: 5))\nshared.off_change(ui)\n\\swap(shared, (a) -> Account(owner: a.owner, balance: 5))\n\\swap(shared, (a) -> Account(owner: a.owner, balance: 9))\nshared.balance -% db\n\\swap(shared, (a) -> Account(owner: a.owner, balance: 1))\n', "run", "db 0 -> 5\nui 5\ndb 5 -> 9"),
 ("observers are not called for a different property",
  'tuple A\n  x Int,\n  property p Int = 0\n  property q Int = 0\ns = Atom[A](A(x: 1))\n_t = s.p +% fn (o, n) -> println("p")\n\\swap(s, (a) -> A(x: 1, p: 0, q: 5))\nprintln("done")\n', "run", "done"),
 ("a property[n] limit stops extra observers",
  'tuple A\n  property[1] p Int = 0\ns = Atom[A](A())\n_a = s.p +% fn (o, n) -> println("a")\n_b = s.p +% fn (o, n) -> println("b")\n', "nogc-fail", "already has 1 observers"),
 ("a lazy binding is read like a plain one",
  'fn sq(n Int) Int\n  n * n\nlazy total = sq(12)\nlazy other Int = total + 1\nprintln("${total} ${total} ${other}")\n', "run", "144 144 145"),
 ("a lazy binding must be pure",
  'lazy x = println("hi")\nprintln(1)\n', "fail", "must be pure"),
 ("a computed property can't have a default",
  'tuple R\n  w Int,\n  property t Int = 5\n    get -> w\nprintln(1)\n', "fail", "has no storage"),
 ("a setter that never stores is an error",
  'tuple R\n  property n Int = 0\n    set(v)\n      println(v)\nprintln(1)\n', "fail", "never stores into `field`"),
 ("did_set needs stored value",
  'tuple R\n  w Int,\n  property t Int\n    get -> w\n    did_set(old)\n      println(old)\nprintln(1)\n', "fail", "did_set"),
 ("a static property has no setter",
  'tuple R\n  static property s Int = 1\n    set(v)\n      field = v\nprintln(1)\n', "fail", "read-only"),
 ("replace writes a property through its setter",
  'tuple Account\n  property balance Int = 0\n    set(value)\n      assert(value >= 0)\n      field = value\ntuple Bank\n  acct Account\nb = Bank(acct: Account(balance: 5))\nprintln(replace(b, /Bank/acct/balance, 9).acct.balance)\nprintln(replace(b, /Bank/acct/balance, 0 - 3).acct.balance)\n', "fail", "assertion failed"),
 ("a spread copies stored values",
  'tuple Account deriving eq\n  owner String,\n  property balance Int = 0\n    set(value)\n      assert(value >= 0)\n      field = value\na = Account(owner: "Ann", balance: 5)\nd = Account(...a, owner: "Bo")\nprintln("${d.owner} ${d.balance} ${a == d}")\n', "run", "Bo 5 false"),
 ("self.field = v updates the receiver of a ref method, through the setter",
  'tuple C\n  property n Int = 1\n    set(v)\n      assert(v < 100)\n      field = v\nimpl C\n  fn (ref Self) bump() Unit\n    self.n = n + 1\nc = C()\nc.bump()\nprintln(c.n)\n', "run", "2"),
 ("self.field = v in a method that is not ref is an error",
  'tuple C\n  n Int\nimpl C\n  fn bump() Unit\n    self.n = n + 1\nprintln(1)\n', "fail", "only a local copy"),
 ("will_set runs before the setter, with the old value still stored, and did_set after",
  'tuple A\n  property n Int = 0\n    will_set(new)\n      println("will ${field} ${new}")\n    set(v)\n      field = v * 2\n    did_set(old)\n      println("did ${old} ${field}")\nimpl A\n  fn (ref Self) put(x Int) Unit\n    n = x\na = A(n: 1)\nprintln("built")\na.put(0)\na.put(5)\n', "run", "built\nwill 2 0\ndid 2 0\nwill 0 5\ndid 0 10"),
 ("will_set is skipped at construction and for an unchanged value",
  'tuple A\n  property n Int = 3\n    will_set(new)\n      println("will ${new}")\nimpl A\n  fn (ref Self) put(x Int) Unit\n    n = x\na = A()\na.put(3)\nprintln("done")\n', "run", "done"),
 ("will_set needs a stored value",
  'tuple R\n  w Int,\n  property t Int\n    get -> w\n    will_set(new)\n      println(new)\nprintln(1)\n', "fail", "will_set"),
 ("a field may still be called property",
  'tuple R\n  property Int\nprintln(R(property: 3).property)\n', "run", "3"),
 ("a generic tuple has properties",
  'tuple Box[T]\n  v T,\n  property same T\n    get -> v\nprintln(Box(v: 7).same)\n', "run", "7"),
 ('a setter that returns a Result gives a set_ function that returns the changed copy', 'tuple Account\n  owner String,\n  property balance Int = 0\n    set(value Int) Result[Unit, Error]\n      if value < 0\n        fail(1, "negative")\n      else\n        field = value\n        Ok(())\nwhen Account(owner: "x", balance: 1)\n  Err(e) -> println("rejected")\n  Ok(a) ->\n    when a.set_balance(5)\n      Ok(b) -> println("${b.balance} ${a.balance}")\n      Err(e) -> println("err")\n', 'run', '5 1'),
 ('a failing set_ function returns the Err and leaves the original', 'tuple Account\n  owner String,\n  property balance Int = 0\n    set(value Int) Result[Unit, Error]\n      if value < 0\n        fail(1, "negative")\n      else\n        field = value\n        Ok(())\nwhen Account(owner: "x", balance: 1)\n  Err(e) -> println("rejected")\n  Ok(a) ->\n    when a.set_balance(-5)\n      Ok(b) -> println("changed")\n      Err(e) -> println("err ${a.balance}")\n', 'run', 'err 1'),
 ('construction with a failing setter is a Result', 'tuple Account\n  owner String,\n  property balance Int = 0\n    set(value Int) Result[Unit, Error]\n      if value < 0\n        fail(1, "negative")\n      else\n        field = value\n        Ok(())\nwhen Account(owner: "y", balance: -1)\n  Ok(b) -> println("made")\n  Err(e) -> println("rejected")\n', 'run', 'rejected'),
 ('construction that passes is Ok', 'tuple Account\n  owner String,\n  property balance Int = 0\n    set(value Int) Result[Unit, Error]\n      if value < 0\n        fail(1, "negative")\n      else\n        field = value\n        Ok(())\nwhen Account(owner: "y", balance: 3)\n  Ok(b) -> println("made ${b.balance}")\n  Err(e) -> println("rejected")\n', 'run', 'made 3'),
 ('plain assignment to a property whose setter can fail is an error', 'tuple Account\n  owner String,\n  property balance Int = 0\n    set(value Int) Result[Unit, Error]\n      if value < 0\n        fail(1, "negative")\n      else\n        field = value\n        Ok(())\nwhen Account(owner: "y")\n  Ok(a) -> a.balance = 4\n  Err(e) -> println("no")\n', 'fail', 'can fail'),
 ("a Result setter can't be priv", 'tuple A\n  property n Int = 0\n    priv set(v Int) Result[Unit, Error]\n      field = v\n      Ok(())\nprintln(1)\n', 'fail', "can't be `priv set`"),
 ("a setter's return type must be a Result", 'tuple A\n  property n Int = 0\n    set(v Int) Int\n      field = v\n      1\nprintln(1)\n', 'fail', 'returns a `Result`'),
 ('a failing delegate gets a set_ function that returns the changed copy', 'tuple Percent\n  value Int\nimpl FieldHandler[Int] for Percent\n  fn get_value() Int\n    value\n  fn (ref Self) set_value(new_value Int) Result[Unit, Error]\n    if new_value < 0\n      fail(1, "negative")\n    else\n      value = new_value\n      Ok(())\ntuple Gauge\n  level Int delegate(Percent)\nwhen Gauge(level: 5)\n  Err(e) -> println("rejected")\n  Ok(g) ->\n    when g.set_level(8)\n      Ok(h) -> println("${h.level} ${g.level}")\n      Err(e) -> println("no")\n', 'run', '8 5'),
 ("a failing delegate's set_ function returns the Err and leaves the original", 'tuple Percent\n  value Int\nimpl FieldHandler[Int] for Percent\n  fn get_value() Int\n    value\n  fn (ref Self) set_value(new_value Int) Result[Unit, Error]\n    if new_value < 0\n      fail(1, "negative")\n    else\n      value = new_value\n      Ok(())\ntuple Gauge\n  level Int delegate(Percent)\nwhen Gauge(level: 5)\n  Err(e) -> println("rejected")\n  Ok(g) ->\n    when g.set_level(-8)\n      Ok(h) -> println("changed")\n      Err(e) -> println("rejected, still ${g.level}")\n', 'run', 'rejected, still 5'),
 ('construction through a failing delegate is a Result', 'tuple Percent\n  value Int\nimpl FieldHandler[Int] for Percent\n  fn get_value() Int\n    value\n  fn (ref Self) set_value(new_value Int) Result[Unit, Error]\n    if new_value < 0\n      fail(1, "negative")\n    else\n      value = new_value\n      Ok(())\ntuple Gauge\n  level Int delegate(Percent)\nwhen Gauge(level: -1)\n  Ok(g) -> println("made")\n  Err(e) -> println("rejected")\n', 'run', 'rejected'),
 ('assignment to a delegate field that can fail is an error', 'tuple Percent\n  value Int\nimpl FieldHandler[Int] for Percent\n  fn get_value() Int\n    value\n  fn (ref Self) set_value(new_value Int) Result[Unit, Error]\n    if new_value < 0\n      fail(1, "negative")\n    else\n      value = new_value\n      Ok(())\ntuple Gauge\n  level Int delegate(Percent)\nwhen Gauge(level: 5)\n  Ok(g) -> g.level = 3\n  Err(e) -> println("no")\n', 'fail', 'can reject a value'),
 ('replace through a failing delegate aborts on a rejected value', 'tuple Percent\n  value Int\nimpl FieldHandler[Int] for Percent\n  fn get_value() Int\n    value\n  fn (ref Self) set_value(new_value Int) Result[Unit, Error]\n    if new_value < 0\n      fail(1, "negative")\n    else\n      value = new_value\n      Ok(())\ntuple Gauge\n  level Int delegate(Percent)\nwhen Gauge(level: 5)\n  Ok(g) ->\n    r = replace(g, /Gauge/level, -3)\n    println("x")\n  Err(e) -> println("no")\n', 'fail', 'rejected the value'),
 ('replace through a delegate runs the delegate', 'tuple Percent\n  value Int\nimpl FieldHandler[Int] for Percent\n  fn get_value() Int\n    value\n  fn (ref Self) set_value(new_value Int) Result[Unit, Error]\n    if new_value < 0\n      fail(1, "negative")\n    else\n      value = new_value\n      Ok(())\ntuple Gauge\n  level Int delegate(Percent)\nwhen Gauge(level: 5)\n  Ok(g) ->\n    r = replace(g, /Gauge/level, 7)\n    println("${r.level}")\n  Err(e) -> println("no")\n', 'run', '7'),
 ('a hand-written set_ is fine when nothing is generated', 'tuple Account\n  owner String,\n  property balance Int = 0\nimpl Account\n  fn set_balance(v Int) Result[Account, Error]\n    if v < 0\n      fail(1, "negative")\n    else\n      Ok(Account(owner: owner, balance: v))\nwhen Account(owner: "x", balance: 1).set_balance(-2)\n  Ok(b) -> println("ok")\n  Err(e) -> println("err")\n', 'run', 'err'),
 ('a hand-written set_ clashes with the generated one', 'tuple Account\n  property balance Int = 0\n    set(value Int) Result[Unit, Error]\n      field = value\n      Ok(())\nimpl Account\n  fn set_balance(v Int) Result[Account, Error]\n    Account(balance: v)\nprintln(1)\n', 'fail', 'is generated for a property'),
 ("a hand-written set_ clashes with a failing delegate's", 'tuple Percent\n  value Int\nimpl FieldHandler[Int] for Percent\n  fn get_value() Int\n    value\n  fn (ref Self) set_value(new_value Int) Result[Unit, Error]\n    value = new_value\n    Ok(())\ntuple Gauge\n  level Int delegate(Percent)\nimpl Gauge\n  fn set_level(v Int) Result[Gauge, Error]\n    Gauge(level: v)\nprintln(1)\n', 'fail', 'is generated for a property'),
]

fails = []
for name, src, how, word in CASES:
    for gc in (False, True):
        if how == "nogc-fail" and gc:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        want_fail = how in ("fail", "nogc-fail")
        ok = ((r.returncode != 0) if want_fail else (r.returncode == 0)) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:300]}"))
        if not ok:
            fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
