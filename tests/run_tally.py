"""Static pool tally tests.  Run: python3 tests/run_tally.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
fails = []


def mx(args, src, manifest=None, after=()):
    d = tempfile.mkdtemp(dir=D)
    if manifest is not None:
        open(os.path.join(d, "Moxie.toml"), "w").write(manifest)
    p = os.path.join(d, "t.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", *args, p, *after], cwd=d, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT))
    return r.returncode, r.stdout + r.stderr


def chk(name, args, src, *words, absent=(), want=0, manifest=None, after=()):
    rc, out = mx(args, src, manifest, after)
    import re
    def has(w):
        return re.search(w[3:], out) is not None if w.startswith("re:") else w in out
    good = rc == want and all(has(w) for w in words) and not any(has(w) for w in absent)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:300]}"))
    if not good:
        fails.append(name)


chk("nothing created", ["pools"], 'println("hi")\n', "no counted resource")
chk("sites are counted", ["pools"], 'rx, tx = Chan[Int][1]()\na = Atom(1)\nb = Atom(2)\n', "re:Atom\\s+2\\n", "re:Chan\\s+1\\n", absent=("re:\\d\\+",))
chk("callees are included", ["pools"], 'fn make() ChanW[Int]:\n  rx, tx = Chan[Int][1]()\n  tx\na = make()\nb = make()\n', "re:Chan\\s+2\\n")
chk("a loop gives N+", ["pools"], 'for i in 1..=3:\n  t = after(1ms)\n', "Timer", "1+", "created in a loop", want=1)
chk("a call in a loop gives N+", ["pools"], 'fn one() Atom[Int]: Atom(1)\nfor i in 1..=3:\n  a = one()\n', "Atom", "1+", "created in a loop", want=1)
chk("recursion gives N+", ["pools"], 'fn go(n: Int) Int:\n  a = Atom(n)\n  if n == 0: 0 else: go(n - 1)\nprintln(go(2))\n', "created in recursion", want=1)
chk("a fiber function with no limit has an unknown count", ["pools"], 'fn w(tx: ChanW[Int]) Unit:\n  f = Future[Int]()\n  \\write(tx, 1)\nrx, tx = Chan[Int][1]()\n_ = run w(tx)\n', "re:Future\\s+1\\+", "no limit", "warning: fiber function 'w'")
FB = 'fiber[3] fn feed(tx: ChanW[Int]) Unit:\n  f = Future[Int]()\n  \\write(tx, 1)\nrx, tx = Chan[Int][8]()\n_ = run feed(tx)\n'
chk("fiber[n] multiplies what the fiber creates", ["pools"], FB, "re:Future\\s+3\\n", "re:Chan\\s+1\\n", "largest possible fiber count: 4", absent=("warning",))
chk("the manifest limit is the default", ["pools"], FB.replace("fiber[3] fn", "fn"), "re:Future\\s+2\\n", "largest possible fiber count: 3", manifest="[fibers]\nlimit = 2\n", absent=("warning",))
chk("an annotation beats the manifest default", ["pools"], FB, "re:Future\\s+3\\n", manifest="[fibers]\nlimit = 2\n")
chk("fibers started by fibers are counted from their own limits", ["pools"], 'fiber[2] fn inner() Unit:\n  a = Atom(1)\nfiber[3] fn outer() Unit:\n  _ = run inner()\n  _ = run inner()\n_ = run outer()\n', "re:Atom\\s+2\\n", "largest possible fiber count: 6")
chk("a bad manifest limit is an error", ["pools"], FB, "limit", manifest="[fibers]\nlimit = 0\n", want=2)
chk("an unknown manifest key is an error", ["pools"], FB, "unknown key", manifest="[fibers]\nlimits = 2\n", want=2)
chk("the header is written", ["pools"], FB, "Future", after=("--header", "h.json"))
chk("run gives NO_SLOT when all of a function's slots are alive", ["run"], 'fiber[1] fn one(rx: ChanR[Int]) Unit:\n  _ = read(rx)\nrx, tx = Chan[Int][4]()\nprintln(run one(clone(rx)))\nprintln(run one(clone(rx)))\n\\write(tx, 1)\n', "Ok(())", "code: 5")
chk("a slot is free again when the fiber ends", ["run"], 'fiber[1] fn one(rx: ChanR[Int]) Unit:\n  _ = read(rx)\nrx, tx = Chan[Int][4]()\nprintln(run one(clone(rx)))\n\\write(tx, 1)\nsleep(1ms)\nprintln(run one(clone(rx)))\n\\write(tx, 1)\n', "Ok(())\nOk(())")
chk("a run that fails with NO_SLOT releases the resources it was given", ["run"], 'fiber[1] fn one(done: ChanR[Int], out: ChanW[Int]) Unit:\n  _ = read(done)\n  _ = write(out, 1)\ndr, dw = Chan[Int][1]()\nrx, tx = Chan[Int][4]()\nprintln(run one(clone(dr), clone(tx)))\nprintln(run one(dr, tx))\n_ = write(dw, 1)\nprintln(read(rx))\nprintln(read(rx))\n', "code: 5", "Ok(1)", "channel closed", absent=("deadlock",))
chk("the manifest limit applies to run", ["run"], 'fn one(rx: ChanR[Int]) Unit:\n  _ = read(rx)\nrx, tx = Chan[Int][4]()\nprintln(run one(clone(rx)))\nprintln(run one(clone(rx)))\n\\write(tx, 1)\n\\write(tx, 1)\n', "code: 5", manifest="[fibers]\nlimit = 1\n")
chk("files, sockets, and listeners", ["pools"], 'f = open_file("a", Create)?\nl = listen(0)?\nc = connect("127.0.0.1", port_of(l))?\ns = accept(l)?\n', "Io file", "re:Io socket\\s+2", "Listener")
chk("a connection", ["pools"], 'c = Connection.memory()\n', "Connection")
chk("foreign handles", ["pools"], 'foreign "c":\n  handle File closes fclose\n  impure fn fopen(path: CString, mode: CString) Result[File, Error]\n  impure fn fclose(f: File)\nf = fopen(cstr("/dev/null"), cstr("r"))?\nfclose(move f)\n', "handle File")
chk("--pools run compares with the observed use", ["--pools", "run"], 'a = Atom(1)\nrx, tx = Chan[Int][1]()\nprintln("x")\n', "pool report (observed)", "pool tally (static)", absent=("warning",))
# the closing rule
chk("a file closed in its iteration counts once", ["pools"], 'for i in 1..=3:\n  f = open_file("a", Create)?\n  close(f)\n', "re:Io file\\s+1\\n", absent=("re:\\d\\+",))
chk("a file kept past its iteration is an error", ["pools"], 'tx_r, tx = Chan[Io][4]()\nfor i in 1..=3:\n  f = open_file("a", Create)?\n  \\write(tx, move f)\n', "outlives the iteration", want=1)
chk("the same error stops a run", ["run"], 'rx, tx = Chan[Io][4]()\nfor i in 1..=3:\n  f = open_file("a", Create)?\n  \\write(tx, move f)\n', "outlives the iteration", want=2)
chk("a timer made in a loop is an error", ["pools"], 'for i in 1..=3:\n  t = after(1ms)\n', "Timer is created in a loop", want=1)
chk("a callee that opens and closes may be called in a loop", ["pools"], 'fn peek() Result[Int, Error]:\n  f = open_file("a", Create)?\n  close(f)\n  Ok(1)\nfor i in 1..=3:\n  r = peek()\n', "re:Io file\\s+1\\n", absent=("re:\\d\\+", "error"))
chk("a callee that returns its file is fine when the caller closes it", ["pools"], 'fn opened() Result[Io, Error]: open_file("a", Create)\nfor i in 1..=3:\n  f = opened()?\n  close(f)\n', "re:Io file\\s+1\\n", absent=("re:\\d\\+", "error"))
chk("a callee that returns its file is an error when the caller keeps it", ["pools"], 'fn opened() Result[Io, Error]: open_file("a", Create)\nrx, tx = Chan[Io][4]()\nfor i in 1..=3:\n  f = opened()?\n  \\write(tx, move f)\n', "outlives the call", want=1)
chk("a returned file counts for the caller, not as a loop", ["pools"], 'fn opened() Result[Io, Error]: open_file("a", Create)\nf = opened()?\nclose(f)\n', "re:Io file\\s+1\\n", absent=("re:\\d\\+", "error"))
chk("recursion that keeps a resource is an error", ["pools"], 'fn go(n: Int) Int:\n  a = Atom(n)\n  if n == 0: 0 else: go(n - 1)\nprintln(go(2))\n', "is recursive", want=1)
chk("recursion that closes its file is exact", ["pools"], 'fn go(n: Int) Int:\n  f = open_file("a", Create)?\n  close(f)\n  if n == 0: 0 else: go(n - 1)\nprintln(go(2))\n', "re:Io file\\s+1\\n", absent=("re:\\d\\+", "error"))
chk("moxie/gc has no pools, so no rule", ["--gc", "run"], 'for i in 1..=3:\n  t = after(1ms)\nprintln("ok")\n', "ok")
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
