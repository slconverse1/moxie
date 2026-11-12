"""File watching tests: watch(path).  Run: python3 tests/run_watch.py"""
import os, shutil, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp(prefix="mxwatch")

def run(src, flags=("--allow-all",), cmd="run", t=40):
    src = src.replace("@D@", D)
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", cmd, *flags, f.name], cwd=ROOT, capture_output=True, timeout=t)
        rc, out = r.returncode, r.stdout.decode() + r.stderr.decode()
    except subprocess.TimeoutExpired:
        rc, out = -9, "TIMEOUT"
    os.unlink(f.name)
    return rc, out, time.time() - t0

fails = []
def chk(name, res, rc_want, *wants, under=None, absent=()):
    rc, out, dt = res
    ok = rc == rc_want and all(w in out for w in wants) and not any(a in out for a in absent) and (under is None or dt < under)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}, {dt:.1f}s) {out[:300]!r}"))
    if not ok: fails.append(name)

def fresh():
    shutil.rmtree(D, ignore_errors=True)
    os.makedirs(D)

fresh()
chk("a directory reports created, modified, and deleted", run('''init
  rx = watch("@D@")?
  write_file("@D@/a.txt", "one")?
  c = read(rx)?
  println("${c.kind} ${c.path.ends_with("a.txt")}")
  write_file("@D@/a.txt", "three and more")?
  c = read(rx)?
  println("${c.kind}")
  remove_file("@D@/a.txt")?
  c = read(rx)?
  println("${c.kind}")
  close(rx)
'''), 0, "#created true\n#modified\n#deleted")

fresh()
write = open(D + "/f.txt", "w"); write.write("x"); write.close()
chk("a file reports modified, deleted, then created", run('''init
  rx = watch("@D@/f.txt")?
  write_file("@D@/f.txt", "longer text")?
  println(read(rx)?.kind)
  remove_file("@D@/f.txt")?
  println(read(rx)?.kind)
  write_file("@D@/f.txt", "back")?
  println(read(rx)?.kind)
  close(rx)
'''), 0, "#modified\n#deleted\n#created")

fresh()
chk("a directory is watched one level deep", run('''init
  rx = watch("@D@")?
  make_dir("@D@/sub")?
  c = read(rx)?
  println("${c.kind} ${c.path.ends_with("sub")}")
  write_file("@D@/sub/inner.txt", "x")?
  write_file("@D@/top.txt", "x")?
  c = read(rx)?
  println("${c.kind} ${c.path.ends_with("top.txt")}")
  close(rx)
'''), 0, "#created true\n#created true")

chk("watching nothing is NOT_FOUND", run('init\n  println(watch("@D@/nothing-here"))\n'), 0, "code: 9")
chk("watch needs fs.read (denied)", run('init\n  println(watch("@D@"))\n', ("--allow-read=/nonexistent",)), 0, "code: 10", "fs.read")
chk("watch needs fs (static)", run('init\n  println(watch("@D@"))\n', ("--allow-env",)), 2, "needs fs")
chk("the browser cannot watch", run('init\n  println(watch("@D@"))\n', ("--platform=browser",)), 0, "not available here", "code: 4")
chk("pure code cannot watch", run('pure fn f() Int\n  _ = watch("@D@")\n  1\n', ("--allow-all",), cmd="check"), 1, "uses the system")

fresh()
chk("closing the reader ends the wait, so a real deadlock is still found", run('''init
  rx = watch("@D@")?
  close(rx)
  r, w = Chan[Int][1]()
  println(read(r))
''', t=20), 1, "deadlock", under=15)

fresh()
chk("sleepers keep time while a fiber waits for a change", run('''fiber fn ticker() Unit
  for i in 1..=3
    sleep(50ms)
    println("tick $i")

init
  rx = watch("@D@")?
  _ = run ticker()
  p = spawn("sh", List("-c", "sleep 0.6; echo hi > @D@/late.txt"))?
  println(read(rx)?.kind)
  close(p)
  close(rx)
'''), 0, "tick 1\ntick 2\ntick 3\n#created")

fresh()
chk("a burst the reader does not keep up with is dropped with a warning", run('''init
  rx = watch("@D@")?
  for i in 1..=40
    write_file("@D@/f${i}.txt", "x")?
  sleep(600ms)
  println("done")
'''), 0, "done", "were dropped")

fresh()
chk("the pool tally counts the channel", run('init\n  rx = watch("@D@")?\n  close(rx)\n', (), cmd="pools"), 0, "Chan")
shutil.rmtree(D, ignore_errors=True)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
