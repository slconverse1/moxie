"""Observed pool report tests.  Run: python3 tests/run_pools.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
P = os.path.join(D, "a.txt")
CASES = [
 ("nothing opened", 'println("x")\n', "nothing counted was created"),
 ("files: peak and total", f'a = open_file("{P}", Create)?\nb = open_file("{P}.2", Create)?\nclose(a)\nc = open_file("{P}.3", Create)?\nclose(b)\nclose(c)\n', "Io file"),
 ("peak is 2 for three files", f'a = open_file("{P}", Create)?\nb = open_file("{P}.2", Create)?\nclose(a)\nc = open_file("{P}.3", Create)?\nclose(b)\nclose(c)\n', "   2       3"),
 ("a leaked file still counts", f'a = open_file("{P}", Create)?\n', "Io file     1       1"),
 ("listener and sockets", 'l = listen(0)?\nc = connect("127.0.0.1", port_of(l))?\ns = accept(l)?\nclose(c)\nclose(s)\nclose(l)\n', "Listener"),
 ("channels, futures, timers, atoms", 'rx, tx = Chan[Int][1]()\nwrite(tx, 1)\nr, w = Future[Int]()\nresolve(w, 5)\nt = Timer()\na = Atom(1)\nprintln(read(rx)?)\n', "Chan"),
 ("a resolved future is released", 'r, w = Future[Int]()\nresolve(w, 5)\nr2, w2 = Future[Int]()\nresolve(w2, 6)\n', "Future     1       2"),
 ("connections", 'c = Connection.memory()?\nclose(c)\nd = Connection.memory()?\nclose(d)\n', "Connection"),
]
fails = []
for name, src, word in CASES:
    p = os.path.join(D, "t.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "--pools", "run", p], cwd=ROOT, capture_output=True, text=True)
    good = r.returncode == 0 and word in r.stderr
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={r.returncode} {r.stderr.strip()[:200]!r}"))
    if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
