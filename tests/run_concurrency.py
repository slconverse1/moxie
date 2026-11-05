"""Structured concurrency and cancellation: Cancel, cancel, is_cancelled, `case cancelled(c)`, `scope:`.
Run: python3 tests/run_concurrency.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WORKER = '''fn worker(id: Int, out: ChanW[String], stop: Cancel) Unit:
  while true:
    select:
      case cancelled(stop) ->
        write(out, "worker ${id} stopping")
        return
      case _ ->
        sleep(10ms)

'''

def run(src, flags=(), cmd="run", t=30):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", cmd, *flags, f.name], cwd=ROOT, capture_output=True, timeout=t)
        rc, out = r.returncode, r.stdout.decode() + r.stderr.decode()
    except subprocess.TimeoutExpired:
        rc, out = -9, "TIMEOUT"
    os.unlink(f.name)
    return rc, out

fails = []
def chk(name, src, rc_want, *wants, absent=(), cmd="run"):
    rc, out = run(src, cmd=cmd)
    ok = rc == rc_want and all(w in out for w in wants) and not any(a in out for a in absent)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
    if not ok: fails.append(name)

chk("cancel wakes a worker waiting in select", WORKER + '''rx, tx = Chan[String][10]()
scope s:
  _ = run worker(1, tx, s)
  _ = run worker(2, tx, s)
  sleep(50ms)
  cancel(s)
println(read(rx))
println(read(rx))
println("after")
''', 0, 'worker 1 stopping', 'worker 2 stopping', 'after')

chk("a scope waits for its fibers at the end", '''fn slow(out: ChanW[String]) Unit:
  sleep(100ms)
  write(out, "slow done")

rx, tx = Chan[String][1]()
scope:
  _ = run slow(tx)
  println("body done")
println("after scope")
println(read(rx))
''', 0, 'body done\nafter scope\nOk("slow done")')

chk("an early exit with ? cancels, then waits", WORKER + '''fn job() Result[Int, Error]:
  rx, tx = Chan[String][4]()
  scope s:
    _ = run worker(1, tx, s)
    x = Err(Error(MISSING, "no"))?
    Ok(1)

println(job())
''', 0, 'Err(Error(code:', 'no')

chk("return from a scope cancels it", WORKER + '''fn job() Int:
  rx, tx = Chan[String][4]()
  scope s:
    _ = run worker(1, tx, s)
    return 7
  0

println(job())
''', 0, '7')

chk("is_cancelled", '''c = Cancel()
println(is_cancelled(c))
cancel(c)
println(is_cancelled(c))
cancel(c)
println(is_cancelled(c))
''', 0, 'false\ntrue\ntrue')

chk("a cancelled arm is ready at once when already cancelled", '''c = Cancel()
cancel(c)
select:
  case cancelled(c) -> println("seen")
  case _ -> println("default")
''', 0, 'seen')

chk("nested scopes wait for their own fibers", '''fn task(name: String, ms: Int, out: ChanW[String]) Unit:
  sleep(ms * 1ms)
  write(out, name)

rx, tx = Chan[String][4]()
scope:
  scope:
    _ = run task("inner", 20, tx)
  println("inner scope over")
  _ = run task("outer", 40, tx)
println("outer scope over")
println(read(rx))
println(read(rx))
''', 0, 'inner scope over\nouter scope over', 'Ok("inner")', 'Ok("outer")')

chk("a fiber started by a scoped fiber is waited for too", '''fn leaf(out: ChanW[String]) Unit:
  sleep(30ms)
  write(out, "leaf")

fn mid(out: ChanW[String]) Unit:
  _ = run leaf(out)

rx, tx = Chan[String][2]()
scope:
  _ = run mid(tx)
println("after")
println(read(rx))
''', 0, 'after\nOk("leaf")')

chk("an abort in a scoped fiber still ends the program", '''fn bad() Unit:
  todo("boom")

scope:
  _ = run bad()
  sleep(10ms)
println("not reached")
''', 1, 'boom', absent=('not reached',))

chk("scope gives the value of its body", '''x = scope:
  21 * 2
println(x)
''', 0, '42')

chk("a scope parks, so a pure function may not use one", '''pure fn f() Int:
  scope:
    1

println(f())
''', 1, 'scope', cmd="check")

chk("scope is still usable as a name", '''scope = 3
println(scope + 1)
''', 0, '4')

print()
print("FAILURES: " + ", ".join(fails) if fails else "all concurrency tests passed")
sys.exit(1 if fails else 0)
