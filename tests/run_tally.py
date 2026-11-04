"""Static pool tally tests.  Run: python3 tests/run_tally.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
fails = []


def mx(args, src):
    p = os.path.join(D, "t.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", *args, p], cwd=D, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT))
    return r.returncode, r.stdout + r.stderr


def chk(name, args, src, *words, absent=()):
    rc, out = mx(args, src)
    import re
    def has(w):
        return re.search(w[3:], out) is not None if w.startswith("re:") else w in out
    good = rc == 0 and all(has(w) for w in words) and not any(has(w) for w in absent)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:300]}"))
    if not good:
        fails.append(name)


chk("nothing created", ["pools"], 'println("hi")\n', "no counted resource")
chk("sites are counted", ["pools"], 'rx, tx = Chan[Int][1]()\na = Atom(1)\nb = Atom(2)\n', "re:Atom\\s+2\\n", "re:Chan\\s+1\\n", absent=("re:\\d\\+",))
chk("callees are included", ["pools"], 'fn make() ChanW[Int]:\n  rx, tx = Chan[Int][1]()\n  tx\na = make()\nb = make()\n', "re:Chan\\s+2\\n")
chk("a loop gives N+", ["pools"], 'for i in 1..=3:\n  t = after(1ms)\n', "Timer", "1+", "created in a loop")
chk("a call in a loop gives N+", ["pools"], 'fn one() Atom[Int]: Atom(1)\nfor i in 1..=3:\n  a = one()\n', "Atom", "1+", "created in a loop")
chk("recursion gives N+", ["pools"], 'fn go(n: Int) Int:\n  a = Atom(n)\n  if n == 0: 0 else: go(n - 1)\nprintln(go(2))\n', "created in recursion")
chk("fiber code counts once per live fiber", ["pools"], 'fn w(tx: ChanW[Int]):\n  f = Future[Int]()\n  write(tx, 1)\nrx, tx = Chan[Int][1]()\nrun w(tx)\n', "Future", "fiber", "Chan")
chk("files, sockets, and listeners", ["pools"], 'f = open_file("a", Create)?\nl = listen(0)?\nc = connect("127.0.0.1", port_of(l))?\ns = accept(l)?\n', "Io file", "re:Io socket\\s+2", "Listener")
chk("a connection", ["pools"], 'c = Connection.memory()\n', "Connection")
chk("foreign handles", ["pools"], 'foreign "c":\n  handle File closes fclose\n  impure fn fopen(path: CString, mode: CString) Result[File, Error]\n  impure fn fclose(f: File)\nf = fopen(cstr("/dev/null"), cstr("r"))?\nfclose(move f)\n', "handle File")
chk("--pools run compares with the observed use", ["--pools", "run"], 'a = Atom(1)\nrx, tx = Chan[Int][1]()\nprintln("x")\n', "pool report (observed)", "pool tally (static)", absent=("warning",))
chk("a loop that closes each file is observed as one open", ["--pools", "run"], 'for i in 1..=3:\n  f = open_file("a", Create)?\n  close(f)\n', "Io file", "1+", "created in a loop")
# the exact static count is never below what a run observes
for name in sorted(os.listdir(os.path.join(ROOT, "examples"))):
    if name.endswith(".mxi") and name not in ("echo_server.mxi", "stdin_to_socket.mxi"):
        p = os.path.join(ROOT, "examples", name)
        r = subprocess.run([sys.executable, "-m", "moxie", "--pools", "run", p], cwd=D, capture_output=True, text=True,
                           env=dict(os.environ, PYTHONPATH=ROOT), input="", timeout=60)
        good = "warning: observed" not in r.stderr
        print(("ok    " if good else "FAIL  ") + f"example {name}: static tally is not below the observed use")
        if not good:
            fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
