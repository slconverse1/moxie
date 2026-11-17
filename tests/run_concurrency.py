"""Structured concurrency and cancellation: Cancel, cancel, is_cancelled, `case cancelled(c)`, `wait`.
Run: python3 tests/run_concurrency.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WORKER = '''fiber fn worker(id Int, out ChanW[String], stop Cancel) Unit
  while true
    select
      cancelled(stop) ->
        \\write(out, "worker ${id} stopping")
        return
      _ ->
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
wait s
  _ = go worker(1, clone(tx), s)
  _ = go worker(2, tx, s)
  sleep(50ms)
  cancel(s)
println(read(rx))
println(read(rx))
println("after")
''', 0, 'worker 1 stopping', 'worker 2 stopping', 'after')

chk("a wait block waits for its fibers at the end", '''fiber fn slow(out ChanW[String]) Unit
  sleep(100ms)
  \\write(out, "slow done")

rx, tx = Chan[String][1]()
wait
  _ = go slow(tx)
  println("body done")
println("after wait")
println(read(rx))
''', 0, 'body done\nafter wait\nOk("slow done")')

chk("an early exit with ? cancels, then waits", WORKER + '''fn job() Result[Int, Error]
  rx, tx = Chan[String][4]()
  wait s
    _ = go worker(1, tx, s)
    x = Err(Error(MISSING, "no"))?
    Ok(1)

println(job())
''', 0, 'Err(Error(code:', 'no')

chk("return from a wait block cancels it", WORKER + '''fn job() Int
  rx, tx = Chan[String][4]()
  wait s
    _ = go worker(1, tx, s)
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
select
  cancelled(c) -> println("seen")
  _ -> println("default")
''', 0, 'seen')

chk("nested wait blocks wait for their own fibers", '''fiber fn task(name String, ms Int, out ChanW[String]) Unit
  sleep(ms * 1ms)
  \\write(out, name)

rx, tx = Chan[String][4]()
wait
  wait
    _ = go task("inner", 20, clone(tx))
  println("inner wait over")
  _ = go task("outer", 40, tx)
println("outer wait over")
println(read(rx))
println(read(rx))
''', 0, 'inner wait over\nouter wait over', 'Ok("inner")', 'Ok("outer")')

chk("a fiber started by a scoped fiber is waited for too", '''fiber fn leaf(out ChanW[String]) Unit
  sleep(30ms)
  \\write(out, "leaf")

fiber fn mid(out ChanW[String]) Unit
  _ = go leaf(out)

rx, tx = Chan[String][2]()
wait
  _ = go mid(tx)
println("after")
println(read(rx))
''', 0, 'after\nOk("leaf")')

chk("an abort in a scoped fiber still ends the program", '''fiber fn bad() Unit
  todo("boom")

wait
  _ = go bad()
  sleep(10ms)
println("not reached")
''', 1, 'boom', absent=('not reached',))

chk("wait gives the value of its body", '''x = wait
  21 * 2
println(x)
''', 0, '42')

chk("a wait block parks, so a pure function may not use one", '''pure fn f() Int
  wait
    1

println(f())
''', 1, 'wait', cmd="check")

chk("wait is still usable as a name", '''wait = 3
println(wait + 1)
''', 0, '4')

chk("the old spelling points to the new one", '''scope
  println(1)
''', 2, '`scope` is now `wait`', cmd="check")

# The Try page runs under the browser platform, whose permission check must ignore the walk's effect kinds (parks, uses a resource).
_rc, _out = run('''fiber fn task(name String, ms Int, out ChanW[String]) Unit
  sleep(ms * 1ms)
  \\write(out, name)

rx, tx = Chan[String][4]()
wait
  _ = go task("a", 20, clone(tx))
  _ = go task("b", 40, tx)
println("both are done")
''', flags=("--platform=browser",))
_ok = _rc == 0 and "both are done" in _out and "KeyError" not in _out
print(("ok    " if _ok else "FAIL  ") + "a wait block runs under the browser platform" + ("" if _ok else f"  (rc {_rc}) {_out[:300]!r}"))
if not _ok: fails.append("browser platform")

print()
print("FAILURES: " + ", ".join(fails) if fails else "all concurrency tests passed")
sys.exit(1 if fails else 0)
