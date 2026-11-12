"""fp.trans: transformers and mtl classes (moxie/gc only).  Run: python3 tests/run_trans.py"""
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

IMP = "import fp.trans\n"
ST_EX = "trans.StateT[trans.ExceptT[trans.Identity, String, _], Int, _]"
EX_ST = "trans.ExceptT[trans.StateT[trans.Identity, Int, _], String, _]"

chk("Identity is a monad", IMP + """m = trans.Identity.pure(2).flat_map((a) -> trans.Identity.pure(a + 1)).map((a) -> a * 2)
println(trans.run_identity(m))
""", 0, "6")

chk("StateT over Identity: get, put, modify, gets via the class", IMP + """fn prog[M[_]: Monad + MonadState[Int]]() M[Int]
  M.modify((n) -> n * 2).flat_map((u) -> M.get()).flat_map((n) -> M.put(n + 1)).flat_map((u) -> M.gets((n) -> n * 10))
println(trans.run_identity(trans.run_state_t(prog[trans.StateT[trans.Identity, Int, _]](), 5)))
""", 0, "(110, 11)")

chk("a for: block works in a transformer", IMP + """fn prog[M[_]: Monad + MonadState[Int]]() M[Int]
  for
    a in M.get()
    u in M.put(a + 5)
    b in M.get()
    yield a * b
println(trans.run_identity(trans.run_state_t(prog[trans.StateT[trans.Identity, Int, _]](), 1)))
""", 0, "(6, 6)")

chk("ReaderT: ask, asks, local", IMP + """fn prog[M[_]: Monad + MonadReader[Int]]() M[Int]
  M.ask().flat_map((a) -> M.local((r) -> r * 100, M.asks((r) -> r + 1)).map((b) -> a + b))
println(trans.run_identity(trans.run_reader_t(prog[trans.ReaderT[trans.Identity, Int, _]](), 2)))
""", 0, "203")

chk("WriterT: tell and the log", IMP + """fn prog[M[_]: Monad + MonadWriter[String]]() M[Int]
  M.tell("a").flat_map((u) -> M.tell("b")).map((u) -> 7)
println(trans.run_identity(trans.run_writer_t(prog[trans.WriterT[trans.Identity, String, _]]())))
""", 0, '(7, List("a", "b"))')

chk("ExceptT: throw and catch", IMP + """fn prog[M[_]: Monad + MonadError[String]](bad: Bool) M[Int]
  risky = if bad then M.throw_error("boom") else M.pure(1)
  M.catch_error(risky, (e) -> M.pure(len(e)))
println(trans.run_identity(trans.run_except_t(prog[trans.ExceptT[trans.Identity, String, _]](true))))
println(trans.run_identity(trans.run_except_t(prog[trans.ExceptT[trans.Identity, String, _]](false))))
""", 0, "Ok(4)\nOk(1)")

chk("ExceptT short-circuits", IMP + """fn prog[M[_]: Monad + MonadError[String]]() M[Int]
  M.pure(1).flat_map((a) -> M.throw_error("stop")).flat_map((b) -> M.pure(99))
println(trans.run_identity(trans.run_except_t(prog[trans.ExceptT[trans.Identity, String, _]]())))
""", 0, 'Err("stop")')

TICK = """fn tick[M[_]: Monad + MonadState[Int] + MonadError[String]](limit: Int) M[Int]
  M.get().flat_map((n) -> if n >= limit then M.throw_error("too big") else M.put(n + 1)).flat_map((u) -> M.get())
"""
chk("a stack of StateT over ExceptT: the failure drops the state", IMP + TICK + f"""go = (s: Int): trans.run_identity(trans.run_except_t(trans.run_state_t(tick[{ST_EX}](5), s)))
println(go(1))
println(go(9))
""", 0, 'Ok((2, 2))\nErr("too big")')
chk("the other order, ExceptT over StateT: the state survives the failure", IMP + TICK + f"""go = (s: Int): trans.run_identity(trans.run_state_t(trans.run_except_t(tick[{EX_ST}](5)), s))
println(go(1))
println(go(9))
""", 0, "(Ok(2), 2)\n(Err(\"too big\"), 9)")

chk("state and an error handler together", IMP + f"""f'fn prog[M[_]: Monad + MonadState[Int] + MonadError[String]]() M[Int]\n  M.catch_error(M.put(7).flat_map((u) -> M.throw_error("x")), (e) -> M.get())\nprintln(trans.run_identity(trans.run_except_t(trans.run_state_t(prog['{ST_EX}](), 0))))
println(trans.run_identity(trans.run_state_t(trans.run_except_t(prog[{EX_ST}]()), 0)))
""", 0, "Ok((0, 0))\n(Ok(7), 7)")

THREE = "trans.ReaderT[trans.StateT[trans.WriterT[trans.Identity, String, _], Int, _], Int, _]"
chk("three layers: reader, state, writer, each reached through the others", IMP + f"""f'fn prog[M[_]: Monad + MonadReader[Int] + MonadState[Int] + MonadWriter[String]]() M[Int]\n  M.ask().flat_map((step) -> M.modify((n) -> n + step).flat_map((u) -> M.get()).flat_map((n) -> M.tell("now ${n}").map((u) -> n)))\ninner = trans.run_reader_t(prog['{THREE}](), 10)
println(trans.run_identity(trans.run_writer_t(trans.run_state_t(inner, 1))))
""", 0, '((11, 11), List("now 11"))')

chk("lift: an inner action inside a transformer", IMP + """m = trans.lift_state_t(Ok(5)).flat_map((a) -> trans.StateT[Result[_, Error], Int, _].put(a))
println(trans.run_state_t(m, 0))
""", 0, "Ok(((), 5))")

chk("a StateT over a Result inner monad", IMP + """fn prog[M[_]: Monad + MonadState[Int]]() M[Int]
  M.modify((n) -> n + 1).flat_map((u) -> M.get())
println(trans.run_state_t(prog[trans.StateT[Result[_, Error], Int, _]](), 4))
""", 0, "Ok((5, 5))")

chk("a StateT over List explores every branch", IMP + """m = trans.lift_state_t(List(1, 2)).flat_map((a) -> trans.StateT[List[_], Int, _].modify((n) -> n + a))
println(trans.run_state_t(m, 10))
""", 0, "List(((), 11), ((), 12))")

chk("MonadWriter: listen and censor, also through a StateT", IMP + """fn logit[M[_]: Monad + MonadWriter[String]]() M[Int]
  M.censor((l) -> l + List("!"), M.listen(M.tell("a").flat_map((u) -> M.tell("b")).map((u) -> 5)).flat_map((p) -> M.tell("saw ${len(p(1))}").map((u) -> p(0))))
println(trans.run_identity(trans.run_writer_t(logit[trans.WriterT[trans.Identity, String, _]]())))
println(trans.run_identity(trans.run_writer_t(trans.run_state_t(logit[trans.StateT[trans.WriterT[trans.Identity, String, _], Int, _]](), 0))))
""", 0, '(5, List("a", "b", "saw 2", "!"))\n((5, 0), List("a", "b", "saw 2", "!"))')

chk("ContT: call_cc escapes from a fold", IMP + """fn find_first[M[_]: Monad + MonadCont](xs: List[Int], want: Int) M[Int]
  M.call_cc((leave) -> xs.reduce(M.pure(-1), (acc, x) -> acc.flat_map((r) -> if x == want then leave(x * 100) else M.pure(r))))
fn go(want: Int) Int
  trans.run_identity(trans.run_cont_t(find_first[trans.ContT[trans.Identity, Int, _]](List(1, 2, 3), want), (a) -> trans.Identity.pure(a)))
println("${go(2)} ${go(9)}")
""", 0, "200 -1")

chk("MonadCont through a StateT keeps the state at the escape", IMP + """fn counter[M[_]: Monad + MonadState[Int] + MonadCont]() M[Int]
  M.call_cc((leave) -> M.put(5).flat_map((u) -> leave(1)).flat_map((u) -> M.put(99))).flat_map((a) -> M.get())
fn go() (Int, Int)
  trans.run_identity(trans.run_cont_t(trans.run_state_t(counter[trans.StateT[trans.ContT[trans.Identity, (Int, Int), _], Int, _]](), 0), (p) -> trans.Identity.pure(p)))
println(go())
""", 0, "(5, 5)")

chk("ContT lifts MonadState and an inner monad", IMP + """fn bump[M[_]: Monad + MonadState[Int]]() M[Int]
  M.modify((n) -> n + 1).flat_map((u) -> M.get())
fn go() (Int, Int)
  trans.run_identity(trans.run_state_t(trans.run_cont_t(bump[trans.ContT[trans.StateT[trans.Identity, Int, _], (Int, Int), _]]().flat_map((a) -> trans.lift_cont_t(trans.StateT[trans.Identity, Int, _].gets((s) -> (a, s)))), (p) -> trans.StateT[trans.Identity, Int, _].pure(p)), 4)(0))
println(go())
""", 0, "(5, 5)")

FREE = """enum Cmd[Next]
  Say(String, Next)
  Ask((String) -> Next)
impl Functor[Cmd]
  fn map[A, B](self: Cmd[A], f: (A) -> B) Cmd[B]
    when self
      Say(s, n) -> Say(s, f(n))
      Ask(k) -> Ask((x) -> f(k(x)))
fn dialog[M[_]: Monad + MonadFree[Cmd]]() M[String]
  M.wrap(Say("name?", ())).flat_map((u) -> M.wrap(Ask((x) -> x))).flat_map((n) -> M.wrap(Say("hi ${n}", ())).map((u) -> n))
"""
chk("FreeT over Result: a program interpreted with effects of the inner monad", IMP + FREE + """prog = dialog[trans.FreeT[Cmd, Result[_, Error], _]]()
step = (c: Cmd[Result[List[String], Error]]) -> when c
  Say(s, rest) -> map_ok(rest, (l) -> List(s) + l)
  Ask(k) -> k("sam")
println(trans.fold_free_t(prog, (n) -> Ok(List("done ${n}")), step))
""", 0, 'Ok(List("name?", "hi sam", "done sam"))')

chk("FreeT: an inner failure stops the interpreter", IMP + FREE + """prog = dialog[trans.FreeT[Cmd, Result[_, Error], _]]()
step = (c: Cmd[Result[List[String], Error]]) -> when c
  Say(s, rest) -> map_ok(rest, (l) -> List(s) + l)
  Ask(k) -> Err(Error(MISSING, "no input"))
println(is_err(trans.fold_free_t(prog, (n) -> Ok(List("done")), step)))
""", 0, "true")

chk("these packages are moxie/gc only", "import fp.trans\nprintln(1)\n", 2, "only in moxie/gc", flags=())

print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
