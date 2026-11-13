"""Type lambdas, generic aliases as constructors, and MonadTrans.  Run: python3 tests/run_typelam.py"""
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

ONE = """fn one[M[_] Monad]() M[Int]
  M.pure(1)
"""
chk("a lambda applied where it is written", 'x ([A] -> Result[A, String])[Int] = Ok(3)\nprintln(x)\n', 0, "Ok(3)")
chk("lambdas parse and check in no-GC moxie too", 'x ([A] -> Result[A, String])[Int] = Ok(3)\nprintln(x)\n', 0, "Ok(3)", flags=())
chk("a lambda passed as a constructor", ONE + "println(one[[A] -> Result[A, String]]())\n", 0, "Ok(1)")
chk("a generic alias passed as a constructor", "type alias Fail[A] = Result[A, String]\n" + ONE + "println(one[Fail]())\n", 0, "Ok(1)")
chk("a lambda whose body applies an alias", "type alias Fail[A] = Result[A, String]\n" + ONE + "println(one[[A] -> Fail[A]]())\n", 0, "Ok(1)")
chk("an alias of an alias", "type alias Fail[A] = Result[A, String]\ntype alias Fail2[A] = Fail[A]\n" + ONE + "println(one[Fail2]())\n", 0, "Ok(1)")
chk("a lambda fixes the first argument, which a hole cannot", "type alias Pair2[A, B] = Result[B, A]\n" + ONE + "println(one[[B] -> Pair2[String, B]]())\n", 0, "Ok(1)")
chk("a lambda closes over a type parameter in scope", ONE + """fn outer[E](e E) Result[Int, Error]
  one[[A] -> Result[A, E]]()
println(outer(5))
""", 0, "Ok(1)")
chk("a two-parameter lambda for F[_, _]", 'fn k[F[_, _]]() Int\n  1\nprintln(k[[A, B] -> Result[A, B]]())\n', 0, "1")
chk("a lambda parameter shadows an outer name", 'fn k[A, F[_]]() Int\n  1\nprintln(k[Int, [A] -> Result[A, A]]())\n', 0, "1")

STACK = """import fp.trans
type alias App[A] = trans.StateT[trans.ExceptT[trans.Identity, String, _], Int, A]
fn tick[M[_] Monad + MonadState[Int] + MonadError[String]](limit Int) M[Int]
  M.get().flat_map((n) -> if n >= limit then M.throw_error("too big") else M.put(n + 1)).flat_map((u) -> M.get())
"""
chk("a named stack: tick[App]", STACK + """fn go(s Int) Result[(Int, Int), String]
  trans.run_identity(trans.run_except_t(trans.run_state_t(tick[App](5), s)))
println("${go(1)} ${go(9)}")
""", 0, 'Ok((2, 2)) Err("too big")')
chk("the same stack as an anonymous lambda", STACK + """fn go(s Int) Result[(Int, Int), String]
  trans.run_identity(trans.run_except_t(trans.run_state_t(tick[[A] -> trans.StateT[trans.ExceptT[trans.Identity, String, _], Int, A]](5), s)))
println(go(1))
""", 0, "Ok((2, 2))")
chk("an alias as a type value with its arguments", "import fp.trans\ntype alias Counter[M[_], A] = trans.StateT[M, Int, A]\nprintln(trans.run_state_t(Counter[Result[_, Error], Int].put(3), 0))\n", 0, "Ok(((), 3))")

chk("MonadTrans.lift with a lambda", "import fp.trans\na = trans.lift[[M[_], A] -> trans.StateT[M, Int, A], _, _](Ok(1))\nprintln(trans.run_state_t(a, 7))\n", 0, "Ok((1, 7))")
chk("MonadTrans.lift with an alias that takes a constructor", "import fp.trans\ntype alias CounterT[M[_], A] = trans.StateT[M, Int, A]\nb = trans.lift[CounterT, _, _](Ok(5))\nprintln(trans.run_state_t(b, 0))\n", 0, "Ok((5, 0))")
chk("every transformer is a MonadTrans", """import fp.trans
r = trans.lift[[M[_], A] -> trans.ReaderT[M, Int, A], _, _](Ok(1))
println(trans.run_reader_t(r, 0))
w = trans.lift[[M[_], A] -> trans.WriterT[M, String, A], _, _](Ok(2))
println(trans.run_writer_t(w))
e = trans.lift[[M[_], A] -> trans.ExceptT[M, String, A], _, _](Ok(3))
println(trans.run_except_t(e))
""", 0, "Ok(1)\nOk((2, List()))\nOk(Ok(3))")
chk("a program generic in the transformer", 'import fp.trans\nfn wrapped[T[_[_], _] MonadTrans](n Int) T[Result[_, Error], Int]\n  T.lift(Ok(n))\nprintln(trans.run_state_t(wrapped[[M[_], A] -> trans.StateT[M, Int, A]](4), 9))\n', 0, "Ok((4, 9))")

chk("wrong number of arguments to an applied lambda", 'x ([A] -> Result[A, String])[Int, Int] = Ok(1)\n', 1, "this type lambda takes 1 type argument, but 2 given", cmd="check")
chk("wrong number of arguments to a generic alias", 'type alias Fail[A] = Result[A, String]\nx Fail[Int, Int] = Ok(1)\n', 1, "`Fail` takes 1 type argument, but 2 given", cmd="check")
chk("a lambda of the wrong arity for a constructor parameter", ONE + "println(one[[A, B] -> Result[A, B]]())\n", 1, "is a constructor of 1 type argument, but this one takes 2", cmd="check")
chk("an alias of the wrong arity for a constructor parameter", "type alias P[A, B] = Result[A, B]\n" + ONE + "println(one[P]())\n", 1, "but this one takes 2", cmd="check")
chk("a lambda may not repeat a parameter", 'x ([A, A] -> Result[A, A])[Int, Int] = Ok(1)\n', 1, "same parameter twice", cmd="check")

print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
