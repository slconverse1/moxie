"""Standard input and output tests.  Run: python3 tests/run_stdio.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CASES = [
 ("read_line strips the newline", 'println(read_line()?)\n', b"Ann\r\nBob\n", "run", 0, "Ann\n", ""),
 ("end of input is Err(CLOSED)", 'println(read_line())\n', b"", "run", 0, 'Err(Error(code: 1', ""),
 ("read_all", 'println(len(read_all()?))\n', b"abc\ndef\n", "run", 0, "8\n", ""),
 ("stdin_lines is a stream", 'println(stdin_lines() |> map(trim(_)) |> collect())\n', b"a\n b \n", "run", 0, 'List("a", "b")', ""),
 ("bad UTF-8 is BAD_ENCODING", 'println(read_line())\n', b"\xff\n", "run", 0, "code: 8", ""),
 ("stdout and stderr are values", 'println(stdout, "o")\nprintln(stderr, "e")\neprintln("f")\n', b"", "run", 0, "o\n", "e\nf\n"),
 ("stdout may be passed to a function", 'fn say(out: Io, s: String) Unit:\n  println(out, s)\nsay(stdout, "hi")\nsay(stdout, "again")\n', b"", "run", 0, "hi\nagain\n", ""),
 ("a stream cannot be closed", 'close(stdout)\n', b"", "run", 2, "", "cannot be closed"),
 ("pure fn may not read", 'pure fn f() String: read_all()?\n', b"", "check", 2, "", "parks"),
 ("with_stdin feeds a test", 'test "t":\n  assert_eq(with_stdin("Bob\\n", read_line), Ok("Bob"))\n', b"", "test", 0, "1 passed, 0 failed", ""),
]
fails = []
for name, src, stdin, cmd, rc_want, out_w, err_w in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, input=stdin, capture_output=True)
    os.unlink(f.name)
    rc, o, e = r.returncode, r.stdout.decode(), r.stderr.decode()
    good = (rc == rc_want or (rc_want == 2 and rc != 0)) and out_w in o and err_w in (e if err_w else "")
    if not err_w: good = good
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} out={o!r} err={e[:120]!r}"))
    if not good: fails.append(name)
import time
src = 'fn reader(tx: ChanW[String]) Unit:\n  line = read_line()?\n  \\write(tx, "got ${line}")\nfn ticker(tx: ChanW[Int]) Unit:\n  for i in 1..=3:\n    \\write(tx, i)\nrx, tx = Chan[String][1]()\nrx2, tx2 = Chan[Int][8]()\nrun reader(tx)\nrun ticker(tx2)\nprintln(read(rx2)?)\nprintln(read(rx2)?)\nprintln(read(rx2)?)\nprintln(read(rx)?)\n'
with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
    f.write(src)
pr = subprocess.Popen([sys.executable, "-m", "moxie", "run", f.name], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
time.sleep(1.0)
pr.stdin.write(b"hi\n"); pr.stdin.close()
out = pr.stdout.read().decode().split("\n")
pr.wait(); os.unlink(f.name)
good = out[:4] == ["1", "2", "3", "got hi"]
print(("ok    " if good else "FAIL  ") + "a fiber waiting on stdin does not stop the others  " + ("" if good else repr(out)))
if not good: fails.append("stdin parks")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
