"""System basics tests: clock, random, exit, signals, host facts.  Run: python3 tests/run_system.py"""
import os, signal, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CASES = [
 ("sleep moves the monotonic clock", 't0 = monotonic()\nsleep(100ms)\nprintln((monotonic() - t0).nanos() >= 100000000)\n', [], 0, "true"),
 ("monotonic never goes back", 'a = monotonic()\nb = monotonic()\nprintln(b.nanos() >= a.nanos())\n', [], 0, "true"),
 ("now is the Unix time as a Duration", 'println(now().seconds() > 1.7e9)\n', [], 0, "true"),
 ("a duration converts to millis", 'println((250ms).millis())\nprintln((1500ms).seconds())\nprintln((3s).nanos())\n', [], 0, "250\n1.5\n3000000000"),
 ("random is in [0, 1)", 'x = random()\nprintln(x >= 0.0 and x < 1.0)\n', [], 0, "true"),
 ("random_int is inclusive", 'ok = true\nfor i in 0..200:\n  r = random_int(3, 4)\n  if r < 3 or r > 4: ok = false\nprintln(ok)\n', [], 0, "true"),
 ("random_int checks its range", 'println(random_int(5, 1))\n', [], 1, "above the high end"),
 ("random_bytes gives that many", 'println(len(random_bytes(32)))\n', [], 0, "32"),
 ("a seeded Gen repeats", 'a = seeded(7)\nb = seeded(7)\nprintln(gen_int(a, 0, 1000000) == gen_int(b, 0, 1000000))\nprintln(sample[List[Int]](a) == sample[List[Int]](b))\n', [], 0, "true\ntrue"),
 ("a different seed differs", 'a = seeded(1)\nb = seeded(2)\nprintln(gen_int(a, 0, 1000000000) == gen_int(b, 0, 1000000000))\n', [], 0, "false"),
 ("a program with signals still wakes its sleepers", 'fn work(done: ChanW[Int]) Unit:\n  sleep(300ms)\n  write(done, 1)\n\nrx = signals()\ndone_r, done_w = Chan[Int][1]()\n_ = run work(done_w)\nselect:\n  case read(rx) -> exit(130)\n  case read(done_r) -> println("finished")\n', [], 0, "finished"),
 ("exit sets the code", 'exit(3)\n', [], 3, ""),
 ("exit from a fiber ends the program", 'fn quit() Unit:\n  exit(4)\n_ = run quit()\nsleep(1s)\nprintln("late")\n', [], 4, ""),
 ("exit checks its range", 'exit(300)\n', [], 1, "outside 0 to 255"),
 ("cwd is a path", 'println(len(cwd()) > 0)\n', [], 0, "true"),
 ("os_name is a known name", 'println(os_name())\n', [], 0, "linux"),
 ("hostname and temp_dir", 'println(len(hostname()) > 0)\nprintln(len(temp_dir()) > 0)\n', [], 0, "true\ntrue"),
 ("home_dir is a Result", 'println(is_ok(home_dir()) or is_err(home_dir()))\n', [], 0, "true"),
 ("stdout is not a terminal here", 'println(is_terminal(stdout))\nprintln(is_err(terminal_size()))\n', [], 0, "false\ntrue"),
 ("lookup_host finds localhost", 'println(lookup_host("localhost"))\n', [], 0, "127.0.0.1"),
 ("lookup_host reports an unknown name", 'println(lookup_host("no-such-host.invalid"))\n', [], 0, "name not found"),
 ("lookup_host needs net (static)", 'println(lookup_host("localhost"))\n', ["--allow-read"], 2, "needs net"),
 ("lookup_host is checked against the host", 'println(lookup_host("localhost"))\n', ["--allow-connect=example.com:*"], 0, "code: 10"),
 ("make_temp_file makes a file", 'p = make_temp_file("mx-")?\nprintln(path_exists(p))\nremove_file(p)?\n', [], 0, "true"),
 ("make_temp_dir makes a directory", 'p = make_temp_dir("mx-")?\nprintln(path_exists(p))\nremove_dir(p)?\n', [], 0, "true"),
 ("temp files are checked against fs.write", 'println(make_temp_file("mx-"))\n', ["--allow-read"], 0, "code: 10"),
 ("a pure fn may not use the clock", 'pure fn f() Int: nanos(now())\n', [], 2, "uses the system"),
 ("a pure fn may not draw a random number", 'pure fn f() Int: random_int(1, 6)\n', [], 2, "uses the system"),
 ("a forall body may not use the system", 'test "t":\n  forall x: Int:\n    assert(random() < 2.0)\n', [], 2, "uses the system"),
 ("a prints fn must be declared impure for the clock", 'prints fn f() Unit:\n  println(now())\n', [], 2, "declared impure"),
]
fails = []
for name, src, flags, rc_want, out_w in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = "check" if rc_want == 2 and not flags else "run"
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    rc, o = r.returncode, r.stdout.decode() + r.stderr.decode()
    ok = rc == rc_want and out_w in o
    if rc_want == 2 and not flags:
        ok = rc == 1 and out_w in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {o[:300]!r}"))
    if not ok:
        fails.append(name)

# signals: the program waits on the channel; SIGINT and SIGTERM arrive as keywords
SIG = 'rx = signals()\nprintln("ready")\nfor i in 0..2:\n  s = read(rx)?\n  println("got ${s}")\n'
with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
    f.write(SIG)
p = subprocess.Popen([sys.executable, "-m", "moxie", "run", f.name], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
line = p.stdout.readline().decode().strip()
good = line == "ready"
if good:
    p.send_signal(signal.SIGINT)
    time.sleep(0.3)
    p.send_signal(signal.SIGTERM)
try:
    out, err = p.communicate(timeout=15)
except subprocess.TimeoutExpired:
    p.kill()
    out, err = p.communicate()
    good = False
os.unlink(f.name)
out = out.decode()
good = good and "got #interrupt" in out and "got #terminate" in out and p.returncode == 0
print(("ok    " if good else "FAIL  ") + "signals arrive as keywords on a channel" + ("" if good else f"  {out!r} {err.decode()[:200]!r} rc={p.returncode}"))
if not good:
    fails.append("signals")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
