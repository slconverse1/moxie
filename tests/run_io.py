"""File and socket tests.  Run: python3 tests/run_io.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
P = os.path.join(D, "a.txt")
CASES = [
 ("write then read a file", f'w = open_file("{P}", Create)?\nprintln(w, "one")\nprintln(w, "two")\nclose(w)\nr = open_file("{P}", ReadOnly)?\nprintln(read_line(r)?)\nprintln(lines(r) |> collect())\nclose(r)\n', 0, 'one\nList("two")'),
 ("Append adds to the end", f'w = open_file("{P}", Append)?\nprintln(w, "three")\nclose(w)\nprintln(read_file("{P}")?)\n', 0, "one\ntwo\nthree"),
 ("missing file is NOT_FOUND", 'println(open_file("/no/such/file", ReadOnly))\n', 0, "code: 9"),
 ("read_file and write_file", f'write_file("{P}.2", "héllo")?\nprintln(read_file("{P}.2")?)\n', 0, "héllo"),
 ("bad UTF-8 file", f'w = open_file("{P}.3", Create)?\nwrite_bytes(w, b"\\xff")?\nclose(w)\nprintln(read_file("{P}.3"))\n', 0, "code: 8"),
 ("copying a file needs move", f'x = open_file("{P}", ReadOnly)?\ny = x\n', 2, "is a resource"),
 ("pure fn may not read a file", 'pure fn f() String: read_file("a")?\n', 2, "parks"),
 ("a file left open is closed at exit", f'w = open_file("{P}.4", Create)?\nprintln(w, "kept")\n', 0, ""),
 ("sockets: connect, accept, talk", 'l = listen(0)?\nc = connect("127.0.0.1", port_of(l))?\ns = accept(l)?\nprintln(c, "ping")\nprintln(read_line(s)?)\nprintln(s, "pong")\nprintln(read_line(c)?)\nclose(c)\nprintln(read_line(s))\nclose(s)\nclose(l)\n', 0, "ping\npong\nErr(Error(code: 1"),
 ("server and client fibers in one program", 'fn server(tx: ChanW[Int]) Result[Unit, Error]:\n  l = listen(0)?\n  \\write(tx, port_of(l))\n  c = accept(l)?\n  println(c, "hello from server")\n  close(c)\n  close(l)\n  Ok(())\nrx, tx = Chan[Int][1]()\nrun server(tx)\nc = connect("127.0.0.1", read(rx)?)?\nprintln(read_line(c)?)\nclose(c)\n', 0, "hello from server"),
 ("connection refused", 'println(connect("127.0.0.1", 1))\n', 0, "code: 11"),
]
fails = []
for name, src, rc_want, word in CASES:
    f = os.path.join(D, "t.mxi")
    open(f, "w").write(src)
    cmd = "check" if rc_want == 2 else "run"
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f], cwd=ROOT, capture_output=True, text=True)
    o = r.stdout + r.stderr
    good = (r.returncode == rc_want or (rc_want == 2 and r.returncode != 0)) and word in o
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={r.returncode} {o.strip()[:200]}"))
    if not good: fails.append(name)
ok = open(P + ".4").read() == "kept\n"
print(("ok    " if ok else "FAIL  ") + "the leaked file was flushed and closed")
if not ok: fails.append("leak")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
