"""timeout: on waiting calls, the TIMED_OUT code, race, and with_timeout.  Each program runs in both dialects with the same output.
Run: python3 tests/run_timeouts.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITE = 'fn polite(c: Cancel) Result[Int, Error]:\n  while true:\n    select:\n      case cancelled(c) ->\n        return Err(Error(CLOSED, "cancelled"))\n      case _ ->\n        sleep(5ms)\n  Ok(0)\nfn quick(c: Cancel) Result[Int, Error]:\n  sleep(10ms)\n  Ok(42)\n'
STUBBORN = 'done = Atom[Bool](false)\nfn stubborn(c: Cancel) Result[Int, Error]:\n  sleep(200ms)\n  _ = reset(done, true)\n  Ok(7)\n'
CASES = [
 ("read times out on an empty channel", 'rx, tx = Chan[Int][1]()\nr = read(rx, timeout: 50ms)\nprintln(is_err(r))\nprintln(r)\nclose(tx)\n', 'true\nErr(Error(code: 12, message: "read: timed out"))'),
 ("read returns a ready value", 'rx, tx = Chan[Int][1]()\n_ = write(tx, 7)\nprintln(read(rx, timeout: 50ms))\nclose(tx)\n', "Ok(7)"),
 ("a timed-out read takes nothing", 'rx, tx = Chan[Int][1]()\n_ = read(rx, timeout: 10ms)\n_ = write(tx, 9)\nprintln(read(rx, timeout: 10ms))\nclose(tx)\n', "Ok(9)"),
 ("read on a closed channel is CLOSED, not a timeout", 'rx, tx = Chan[Int][1]()\nclose(tx)\nprintln(read(rx, timeout: 1s))\n', 'Err(Error(code: 1, message: "channel closed"))'),
 ("a value that arrives in time wins", 'fiber[1] fn later(out: ChanW[Int]) Unit:\n  sleep(20ms)\n  _ = write(out, 5)\n  close(out)\nrx, tx = Chan[Int][1]()\n_ = run later(move tx)\nprintln(read(rx, timeout: 1s))\n', "Ok(5)"),
 ("wait_child times out", 'c = spawn("sleep", List("2"))?\nprintln(wait_child(c, timeout: 100ms))\nkill_child(c)\nprintln(wait_child(c, timeout: 5s))\n', 'Err(Error(code: 12, message: "wait_child: timed out"))\nOk(137)'),
 ("run_command times out with TIMED_OUT", 'println(run_command("sleep", List("2"), timeout: 100ms))\n', 'Err(Error(code: 12, message: "sleep: timed out"))'),
 ("accept times out", 'l = listen(0)?\nprintln(accept(l, timeout: 100ms))\nclose(l)\n', 'Err(Error(code: 12, message: "accept: timed out"))'),
 ("read_line on a socket times out, then reads", 'l = listen(0)?\nio = connect("127.0.0.1", port_of(l), timeout: 1s)?\nsrv = accept(l, timeout: 1s)?\nprintln(read_line(io, timeout: 100ms))\nprintln(srv, "hello")\nprintln(read_line(io, timeout: 1s))\nclose(srv)\nclose(io)\nclose(l)\n', 'Err(Error(code: 12, message: "read_line: timed out"))\nOk("hello")'),
 ("connect refused is not a timeout", 'println(connect("127.0.0.1", 1, timeout: 1s))\n', 'Err(Error(code: 11, message: "127.0.0.1:1: Connection refused"))'),
 ("race gives the first result", POLITE + 'println(race(polite, quick))\nprintln(race(quick, polite))\n', "Ok(42)\nOk(42)"),
 ("race gives the first result even when it is an Err", POLITE + 'fn fails(c: Cancel) Result[Int, Error]:\n  Err(Error(NOT_FOUND, "no"))\nprintln(race(fails, quick))\n', 'Err(Error(code: 9, message: "no"))'),
 ("race waits for a loser that ignores its token", STUBBORN + 'fn fast(c: Cancel) Result[Int, Error]:\n  Ok(1)\nprintln(race(fast, stubborn))\nprintln(@done)\n', "Ok(1)\ntrue"),
 ("with_timeout passes a result through", POLITE + 'println(with_timeout(1s, quick))\n', "Ok(42)"),
 ("with_timeout gives TIMED_OUT and cancels", POLITE + 'println(with_timeout(50ms, polite))\n', 'Err(Error(code: 12, message: "with_timeout: timed out"))'),
 ("with_timeout waits for a function that ignores its token", STUBBORN + 'println(with_timeout(20ms, stubborn))\nprintln(@done)\n', 'Err(Error(code: 12, message: "with_timeout: timed out"))\ntrue'),
 ("retry around with_timeout", POLITE + 'fn once() Result[Int, Error]:\n  with_timeout(1s, quick)\nprintln(retry(2, 1ms, once))\n', "Ok(42)"),
 ("retry repeats a timeout", 'n = Atom[Int](0)\nfn slow() Result[Int, Error]:\n  _ = swap(n, _ + 1)\n  Err(Error(TIMED_OUT, "slow"))\n_ = retry(3, 1ms, slow)\nprintln(@n)\n', "3"),
]
BAD = [
 ("retry takes a Duration", 'r = retry(2, 5, fn (): Ok(1))\n', "`retry` can't take (Int, Int"),
 ("with_timeout takes a Duration", 'r = with_timeout("x", fn (c): Ok(1))\n', "`with_timeout` can't take (String"),
 ("sleep takes a Duration", 'sleep(3)\n', "`sleep` can't take (Int)"),
 ("race needs two functions", 'x = race(1, 2)\n', "`race` can't take"),
 ("accept has no such option", 'l = listen(0)?\nc = accept(l, nope: 1)\n', "`accept` has no option `nope`"),
]
fails = []
POOLS = [("race and with_timeout count their fibers", POLITE + 'println(race(polite, quick))\nprintln(with_timeout(1s, quick))\n', ["race@", "(limit 2)", "with_timeout@", "(limit 1)", "largest possible fiber count: 4"])]


def run(cmd, src, gc=False):
    f = os.path.join(tempfile.mkdtemp(), "main.mxi")
    open(f, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + [cmd, f], cwd=ROOT, capture_output=True, timeout=60)
    return r.returncode, r.stdout.decode() + r.stderr.decode()


for name, src, want in CASES:
    a, b = run("run", src), run("run", src, True)
    ok = a[0] == 0 and a == b and a[1].strip() == want
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {a[1][:300]!r} / {b[1][:200]!r}"))
    if not ok:
        fails.append(name)
for name, src, want in BAD:
    rc, o = run("check", src)
    ok = rc != 0 and want in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name)
for name, src, wants in POOLS:
    rc, o = run("pools", src)
    ok = rc == 0 and all(w in o for w in wants)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
