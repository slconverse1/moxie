"""Unix socket and named pipe tests.  Run: python3 tests/run_pipes.py"""
import os, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp(prefix="mxpipe")
SOCK, FIFO = D + "/s.sock", D + "/p.fifo"

def run(src, flags=("--allow-all",), cmd="run", t=40):
    src = src.replace("@SOCK@", SOCK).replace("@FIFO@", FIFO)
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", cmd, *flags, f.name], cwd=ROOT, capture_output=True, timeout=t)
        rc, out = r.returncode, r.stdout.decode() + r.stderr.decode()
    except subprocess.TimeoutExpired:
        rc, out = -9, "TIMEOUT"
    os.unlink(f.name)
    for p in (SOCK, FIFO):
        if os.path.exists(p) and cmd == "run" and "keep" not in flags:
            try: os.unlink(p)
            except OSError: pass
    return rc, out, time.time() - t0

fails = []
def chk(name, res, rc_want, *wants, absent=(), under=None):
    rc, out, dt = res
    ok = rc == rc_want and all(w in out for w in wants) and not any(a in out for a in absent) and (under is None or dt < under)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}, {dt:.1f}s) {out[:300]!r}"))
    if not ok: fails.append(name)

ECHO = '''fn serve(l: Listener) Unit:
  c = accept(l)?
  for line in lines(c):
    println(c, "echo $line")
  close(c)

init:
  l = listen_unix("@SOCK@")?
  _ = run serve(move l)
  c = connect_unix("@SOCK@")?
  println(c, "hi")
  println(read_line(c)?)
  println(c, "again")
  println(read_line(c)?)
  close(c)
'''
chk("a Unix socket echoes", run(ECHO), 0, "echo hi\necho again")
chk("closing the Listener removes the socket file", run('init:\n  l = listen_unix("@SOCK@")?\n  println(path_exists("@SOCK@")?)\n  close(l)\n  println(path_exists("@SOCK@")?)\n'), 0, "true\nfalse")
chk("a Listener left open removes it at exit", run('init:\n  l = listen_unix("@SOCK@")?\n  println(path_exists("@SOCK@")?)\n  println("done")\n'), 0, "true\ndone")
subprocess.run(["sh", "-c", f"test ! -e {SOCK}"], check=True)
chk("listening where a file exists is IO_ERROR", run('init:\n  write_file("@SOCK@", "x")?\n  println(listen_unix("@SOCK@"))\n'), 0, "code: 11")
chk("connecting to nothing is NOT_FOUND", run('init:\n  println(connect_unix("@SOCK@"))\n'), 0, "code: 9")
chk("a Unix socket needs fs.write (denied)", run('init:\n  println(listen_unix("@SOCK@"))\n', ("--allow-read", "--allow-write=/nonexistent")), 0, "code: 10", "fs.write")
chk("a Unix socket needs fs (static)", run('init:\n  println(listen_unix("@SOCK@"))\n', ("--allow-env",)), 2, "needs fs")
chk("a Unix socket works under a write grant", run('init:\n  l = listen_unix("@SOCK@")?\n  close(l)\n  println("ok")\n', ("--allow-write=" + D,)), 0, "ok")
chk("the browser has no Unix sockets", run('init:\n  println(listen_unix("@SOCK@"))\n', ("--platform=browser",)), 0, "not available here", "code: 4")

READ = '''init:
  make_fifo("@FIFO@")?
  p = spawn("sh", List("-c", "printf 'one\\\\ntwo\\\\n' > @FIFO@"))?
  r = open_file("@FIFO@", ReadOnly)?
  println(read_line(r)?)
  println(read_line(r)?)
  println(read_line(r))
  close(r)
  println(wait_child(p)?)
  close(p)
'''
chk("a named pipe reads what another program wrote", run(READ), 0, "one\ntwo\nErr(", "code: 1", "\n0")
WRITE = '''init:
  make_fifo("@FIFO@")?
  p = spawn("sh", List("-c", "head -n 2 < @FIFO@"))?
  w = open_file("@FIFO@", Create)?
  println(w, "alpha")
  println(w, "beta")
  close(w)
  rx = child_stdout(p)
  println(read_line(rx)?)
  println(read_line(rx)?)
  println(wait_child(p)?)
  close(p)
'''
chk("a named pipe writes to another program", run(WRITE), 0, "alpha\nbeta\n0")
chk("make_fifo twice is IO_ERROR", run('init:\n  make_fifo("@FIFO@")?\n  println(make_fifo("@FIFO@"))\n'), 0, "code: 11")
chk("a named pipe opens one way only", run('init:\n  make_fifo("@FIFO@")?\n  println(open_file("@FIFO@", ReadWrite))\n'), 0, "code: 11", "reading or for writing")
chk("make_fifo needs fs.write", run('init:\n  println(make_fifo("@FIFO@"))\n', ("--allow-read", "--allow-write=/nonexistent")), 0, "code: 10")
chk("the browser has no named pipes", run('init:\n  println(make_fifo("@FIFO@"))\n', ("--platform=browser",)), 0, "not available here")
HELD = '''fn reader(path: String) Unit:
  r = open_file(path, ReadOnly)?
  println(read_line(r))

init:
  make_fifo("@FIFO@")?
  p = spawn("sh", List("-c", "exec sleep 30 > @FIFO@"))?
  _ = run reader("@FIFO@")
  println("main done")
'''
chk("a read still waiting does not hold up exit", run(HELD), 0, "main done", under=10)
chk("a fiber waiting on a named pipe leaves the others running", run('''fn other() Unit:
  println("other ran")

init:
  make_fifo("@FIFO@")?
  _ = run other()
  p = spawn("sh", List("-c", "sleep 0.3; echo hi > @FIFO@"))?
  r = open_file("@FIFO@", ReadOnly)?
  println(read_line(r)?)
'''), 0, "other ran\nhi")
chk("the pool tally counts a Listener", run('init:\n  l = listen_unix("@SOCK@")?\n  close(l)\n', (), cmd="pools"), 0, "Listener")
os.rmdir(D) if not os.listdir(D) else None
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
