"""fp.state (moxie/gc only).  Run: python3 tests/run_fpstate.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=(), cmd="run", t=240):
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

HEAD = "import fp.state\n\n"

chk("get, put, modify, gets, eval, exec", HEAD + '''m = state.modify((n Int) -> n * 2).flat_map((u) -> state.gets((n Int) -> n + 1))
println(state.eval(m, 5))
println(state.exec(m, 5))
println(state.eval(state.get(), "x"))
println(state.exec(state.put(9), 1))
''', 0, "11\n10\nx\n9")

chk("map and flat_map thread the state", HEAD + '''fn next_id() state.State[Int, Int]
  state.modify((c Int) -> c + 1).flat_map((u) -> state.get())
two = next_id().flat_map((a) -> next_id().map((b) -> (a, b)))
println(two.run(0))
''', 0, "((1, 2), 2)")

chk("branches may return different closures", HEAD + '''fn tick(big Bool) state.State[Int, Unit]
  if big
    state.modify((n Int) -> n + 100)
  else
    state.put(7)
println(state.exec(tick(true), 1))
println(state.exec(tick(false), 1))
''', 0, "101\n7")

chk("traverse runs in order and threads the state", HEAD + '''fn label(name String) state.State[Int, String]
  state.modify((n Int) -> n + 1).flat_map((u) -> state.gets((n Int) -> "${name}${n}"))
println(state.traverse(List("a", "b", "c"), label).run(0))
''', 0, '(List("a1", "b2", "c3"), 3)')

chk("traverse over a long list", HEAD + '''fn add(x Int) state.State[Int, Int]
  state.modify((n Int) -> n + x).flat_map((u) -> state.get())
big = List(i for i in 0..3000)
println(state.exec(state.traverse(big, add), 0))
''', 0, "4498500")

chk("a State can be stored in a list and run later", HEAD + '''steps = List(state.modify((n Int) -> n + 1), state.put(40), state.modify((n Int) -> n + 2))
println(state.exec(steps(2), steps(1).run(0)(1)))
''', 0, "42")

chk("the checker accepts a program that uses it", HEAD + '''println(state.eval(state.get(), 1))
''', 0, "ok", cmd="check")

chk("no-GC moxie refuses at check", HEAD + 'println(1)\n', 1, "only in moxie/gc", flags=(), cmd="check")
chk("no-GC moxie refuses at run", HEAD + 'println(1)\n', 2, "only in moxie/gc", flags=(), cmd="run")

print()
print("FAILURES: " + ", ".join(fails) if fails else "all fp.state tests passed")
sys.exit(1 if fails else 0)
