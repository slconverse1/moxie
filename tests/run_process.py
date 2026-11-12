"""Process tests: run_command, spawn, and the process permission.  Run: python3 tests/run_process.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CASES = [
 ("run_command returns the output", 'r = run_command("echo", List("hello", "world"))?\nprintln("${r.code} [${r.stdout.trim()}]")\n', [], 0, "0 [hello world]"),
 ("a failing program is Ok with its code", 'r = run_command("sh", List("-c", "echo oops >&2; exit 3"))?\nprintln("${r.code} [${r.stderr.trim()}]")\n', [], 0, "3 [oops]"),
 ("stdin text reaches the program", 'r = run_command("cat", stdin: "from stdin")?\nprintln(r.stdout)\n', [], 0, "from stdin"),
 ("no stdin means an empty one, not ours", 'r = run_command("cat")?\nprintln(len(r.stdout))\n', [], 0, "0"),
 ("an unknown program is NOT_FOUND", 'println(run_command("no-such-program-xyz"))\n', [], 0, "code: 9"),
 ("a timeout is an Err", 'println(run_command("sleep", List("5"), timeout: 200ms))\n', [], 0, "timed out"),
 ("cwd sets the directory", 'r = run_command("pwd", cwd: "/tmp")?\nprintln(r.stdout.trim())\n', [], 0, "/tmp"),
 ("env sets the environment", 'r = run_command("sh", List("-c", "echo \\$FOO"), env: Dict("FOO": "bar"))?\nprintln(r.stdout.trim())\n', [], 0, "bar"),
 ("the program gets our env snapshot by default", 'r = run_command("sh", List("-c", "echo [\\$HOME]"))?\nprintln(r.stdout.trim() == "[" + env("HOME").get_or("") + "]")\n', [], 0, "true"),
 ("a program killed by a signal reads as 128 + N", 'r = run_command("sh", List("-c", "kill -9 \\$\\$"))?\nprintln(r.code)\n', [], 0, "137"),
 ("output that is not UTF-8 is BAD_ENCODING", 'r = run_command("printf", List("\\\\377"))\nprintln(r)\n', [], 0, "code: 8"),
 ("a spawned program streams both ways", 'c = spawn("sh", List("-c", "while read x; do echo got \\$x; done"))?\ntx = child_stdin(c)\nrx = child_stdout(c)\nprintln(tx, "one")\nprintln(tx, "two")\nclose(tx)\nprintln(read_line(rx)?)\nprintln(read_line(rx)?)\nprintln(wait_child(c)?)\nclose(c)\n', [], 0, "got one\ngot two\n0"),
 ("kill_child ends it", 'k = spawn("sleep", List("30"))?\nkill_child(k)\nprintln(wait_child(k)?)\nclose(k)\n', [], 0, "137"),
 ("a Child left open is cleaned up at exit", 'k = spawn("sleep", List("30"))?\nprintln("done")\n', [], 0, "done"),
 ("a fiber waiting on a child does not stop the others", 'fiber fn waiter(c: Child, done: ChanW[Int]) Unit\n  _ = wait_child(c)\n  _ = write(done, 1)\n\nc = spawn("sleep", List("1"))?\nd_r, d_w = Chan[Int][1]()\n_ = run waiter(move c, d_w)\nprintln("main goes on")\nprintln(read(d_r)?)\n', [], 0, "main goes on\n1"),
 ("process is checked against the programs granted", 'println(run_command("echo", List("hi")))\n', ["--allow-run=ls"], 0, "code: 10"),
 ("a granted program runs", 'println(run_command("echo", List("hi")))\n', ["--allow-run=echo"], 0, "stdout: \"hi\\n\""),
 ("process needs a grant (static)", 'println(run_command("echo"))\n', ["--allow-read"], 2, "needs process"),
 ("spawn needs a grant too", 'println(spawn("echo"))\n', ["--allow-read"], 2, "needs process"),
 ("--allow-all includes process", 'println(run_command("echo", List("x"))?.stdout)\n', ["--allow-all"], 0, "x"),
 ("the browser has no processes", 'println(run_command("echo"))\n', ["--platform=browser"], 2, "not granted (the browser)"),
]
fails = []
for name, src, flags, rc_want, out_w in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, "run", f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    rc, o = r.returncode, r.stdout.decode() + r.stderr.decode()
    ok = rc == rc_want and out_w in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {o[:300]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
