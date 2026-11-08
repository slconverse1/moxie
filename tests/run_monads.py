"""List, fp.reader, fp.writer, fp.cont, fp.free (moxie/gc only).  Run: python3 tests/run_monads.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=(), cmd="run", t=60):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, f.name], cwd=ROOT, capture_output=True, timeout=t)
        rc, out = r.returncode, r.stdout.decode() + r.stderr.decode()
    except subprocess.TimeoutExpired:
        rc, out = -9, "TIMEOUT"
    os.unlink(f.name)
    return rc, out

fails = []
def chk(name, src, rc_want, *wants, flags=("--gc",), cmd="run"):
    rc, out = run(src, flags, cmd)
    ok = rc == rc_want and all(w in out for w in wants)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
    if not ok: fails.append(name)

chk("map on a List or Array keeps the container (moxie)", """xs = List(1, 2)
a = Array(1, 2)
println(xs.map(_ + 1))
println(a.map(_ + 1))
println(xs |> map(_ * 2))
println(xs.filter(_ > 1) |> collect())
""", 0, "List(2, 3)\nArray(2, 3)\nList(2, 4)\nList(2)", flags=())
chk("map on a List or Array keeps the container (gc)", """xs = List(1, 2)
a = Array(1, 2)
println(xs.map(_ + 1))
println(a.map(_ + 1))
""", 0, "List(2, 3)\nArray(2, 3)")
chk("List is a monad: flat_map, map, pure, ap", """xs = List(1, 2, 3)
println(xs.flat_map((a): List(a, a * 10)))
println(xs.map((a): a + 1))
println(List((a: Int): a + 1).ap(List(1, 2)))
fn two[F[_]: Monad](m: F[Int]) F[Int]:
  m.flat_map((a): F.pure(a * 2))
println(two(List(1, 2)))
""", 0, "List(1, 10, 2, 20, 3, 30)\nList(2, 3, 4)\nList(2, 3)\nList(2, 4)")
chk("for: over lists gives a List", """r = for:
  a in List(1, 2)
  b in List(10, 20)
  yield a + b
println(r)
""", 0, "List(11, 21, 12, 22)")
chk("the List monad laws hold on an example", """f = (a: Int): List(a, a + 1)
g = (a: Int): List(a * 2)
m = List(1, 5)
println(m.flat_map(f).flat_map(g) == m.flat_map((a): f(a).flat_map(g)))
println(List(3).flat_map(f) == f(3))
println(m.flat_map((a): List(a)) == m)
""", 0, "true\ntrue\ntrue")

chk("Reader: ask, asks, local, run_reader", """import fp.reader
tuple Config:
  name: String
  depth: Int
greet = reader.asks((c: Config): "hi ${c.name}").flat_map((g): reader.asks((c: Config): "${g} x${c.depth}"))
println(reader.run_reader(greet, Config("bo", 2)))
println(reader.run_reader(reader.local((c: Config): Config(c.name, 9), greet), Config("bo", 2)))
println(reader.run_reader(reader.ask(), 4))
""", 0, "hi bo x2\nhi bo x9\n4")
chk("Reader: map and a for: block", """import fp.reader
r = for:
  a in reader.asks((n: Int): n + 1)
  b in reader.asks((n: Int): n * 10)
  yield a + b
println(reader.run_reader(r, 3))
""", 0, "34")

chk("Writer: tell, flat_map, map, run_writer", """import fp.writer
w = writer.tell("start").flat_map((u): writer.tell("end")).map((u): 7)
println(writer.run_writer(w))
println(writer.exec_writer(w))
""", 0, '(7, List("start", "end"))\nList("start", "end")')
chk("Writer: listen and censor", """import fp.writer
w = writer.tell(1).flat_map((u): writer.tell(2))
println(writer.run_writer(writer.listen(w)))
println(writer.exec_writer(writer.censor((l: List[Int]): l + List(99), w)))
""", 0, "(((), List(1, 2)), List(1, 2))\nList(1, 2, 99)")
chk("Writer: pure has an empty log", """import fp.writer
println(writer.run_writer(writer.Writer.pure(5)))
""", 0, "(5, List())")

chk("Cont: call_cc escapes", """import fp.cont
safe_div = (a: Int, b: Int): cont.call_cc((leave): if b == 0: leave(-1) else: cont.Cont.pure(a / b))
println(cont.eval_cont(safe_div(10, 2)))
println(cont.eval_cont(safe_div(1, 0)))
""", 0, "5\n-1")
chk("Cont: run_cont with a continuation, and flat_map order", """import fp.cont
m = cont.Cont.pure(2).flat_map((a): cont.Cont.pure(a + 3)).map((a): a * 2)
println(cont.run_cont(m, (a: Int): "got ${a}"))
""", 0, "got 10")

DSL = """import fp.free
enum Cmd[Next]:
  Say(String, Next)
  Ask((String) -> Next)
impl Functor[Cmd]:
  fn map[A, B](self: Cmd[A], f: (A) -> B) Cmd[B]:
    when self:
      Say(s, n) -> Say(s, f(n))
      Ask(k) -> Ask((x): f(k(x)))
say = (s: String): free.lift_f(Say(s, ()))
ask = free.lift_f(Ask((x): x))
"""
chk("Free: a program is data, interpreted by fold_free", DSL + """prog = say("name?").flat_map((u): ask.flat_map((n): say("hello ${n}")))
step = (c: Cmd[List[String]]): when c:
  Say(s, rest) -> List(s) + rest
  Ask(k) -> k("sam")
println(free.fold_free(prog, (u): List(), step))
""", 0, 'List("name?", "hello sam")')
chk("Free: the same program under a second interpreter", DSL + """prog = say("a").flat_map((u): say("b")).flat_map((u): say("c"))
count = (c: Cmd[Int]): when c:
  Say(s, rest) -> rest + 1
  Ask(k) -> k("")
println(free.fold_free(prog, (u): 0, count))
""", 0, "3")

chk("these packages are moxie/gc only", "import fp.reader\nprintln(1)\n", 2, "only in moxie/gc", flags=())

print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
