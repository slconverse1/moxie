"""Ownership tests: moving a resource, and functions that take ownership.  Run: python3 tests/run_moves.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = 'fn eat(c: Child) Unit:\n  close(c)\n\nfn look(c: Child) Int:\n  0\n\n'
CASES = [
 ("a function that closes its parameter must be called with move", HEAD + 'init:\n  c = spawn("true")?\n  eat(c)\n', 1, "takes ownership of `c`", "eat(move c)"),
 ("a move hands it over", HEAD + 'init:\n  c = spawn("true")?\n  eat(move c)\n', 0, "ok"),
 ("using it after the move is an error", HEAD + 'init:\n  c = spawn("true")?\n  eat(move c)\n  println(wait_child(c))\n', 1, "use of moved value `c`"),
 ("moving twice is an error", HEAD + 'init:\n  c = spawn("true")?\n  eat(move c)\n  eat(move c)\n', 1, "use of moved value `c`"),
 ("a function that only looks borrows", HEAD + 'init:\n  c = spawn("true")?\n  println(look(c))\n  println(look(c))\n  close(c)\n', 0, "ok"),
 ("closing after a borrow is fine, closing twice by hand is not moved", HEAD + 'init:\n  c = spawn("true")?\n  _ = look(c)\n  close(c)\n', 0, "ok"),
 ("a function that returns its parameter takes it", 'fn pass(c: Child) Child:\n  c\n\ninit:\n  c = spawn("true")?\n  d = pass(c)\n  close(d)\n', 1, "takes ownership of `c`"),
 ("an explicit return counts too", 'fn pass(c: Child) Child:\n  return c\n\ninit:\n  c = spawn("true")?\n  d = pass(move c)\n  close(d)\n', 0, "ok"),
 ("c.close() inside a function counts", 'fn eat(c: Child) Unit:\n  c.close()\n\ninit:\n  c = spawn("true")?\n  eat(c)\n', 1, "takes ownership"),
 ("moving it on to another function counts", 'fn eat(c: Child) Unit:\n  close(c)\n\nfn outer(c: Child) Unit:\n  eat(move c)\n\ninit:\n  c = spawn("true")?\n  outer(c)\n', 1, "`outer` takes ownership"),
 ("passing a borrow along does not", 'fn look(c: Child) Int:\n  0\n\nfn outer(c: Child) Int:\n  look(c)\n\ninit:\n  c = spawn("true")?\n  println(outer(c))\n  close(c)\n', 0, "ok"),
 ("a named argument is checked", HEAD + 'init:\n  c = spawn("true")?\n  eat(c: c)\n', 1, "takes ownership of `c`"),
 ("a named move is fine", HEAD + 'init:\n  c = spawn("true")?\n  eat(c: move c)\n', 0, "ok"),
 ("a move inside a loop is refused", HEAD + 'init:\n  c = spawn("true")?\n  for i in 1..=2:\n    eat(move c)\n', 1, "moved inside a loop"),
 ("a Terminal handed to a closer needs move", 'fn done(t: Terminal) Unit:\n  close(t)\n\ninit:\n  t = raw_terminal()?\n  done(t)\n', 1, "takes ownership of `t`"),
 ("an Io closed by a function needs move", 'fn done(f: Io) Unit:\n  close(f)\n\ninit:\n  f = open_file("x", ReadOnly)?\n  done(f)\n', 1, "takes ownership of `f`"),
 ("a Listener moved to a fiber still works", 'fn serve(l: Listener) Unit:\n  close(l)\n\ninit:\n  l = listen(0)?\n  _ = run serve(move l)\n', 0, "ok"),
 ("a resource handed to run is gone from the caller", 'fn w(out: ChanW[Int]) Unit:\n  _ = write(out, 1)\n\nrx, tx = Chan[Int][2]()\n_ = run w(tx)\n_ = run w(tx)\n', 1, "use of moved value `tx`"),
 ("a clone feeds the second fiber", 'fn w(out: ChanW[Int]) Unit:\n  _ = write(out, 1)\n\nrx, tx = Chan[Int][2]()\n_ = run w(clone(tx))\n_ = run w(tx)\nprintln(read(rx))\n', 0, "ok"),
 ("using the end after run is an error", 'fn w(out: ChanW[Int]) Unit:\n  _ = write(out, 1)\n\nrx, tx = Chan[Int][2]()\n_ = run w(tx)\n_ = write(tx, 2)\n', 1, "use of moved value `tx`"),
 ("the other end stays usable", 'fn w(out: ChanW[Int]) Unit:\n  _ = write(out, 1)\n\nrx, tx = Chan[Int][2]()\n_ = run w(tx)\nprintln(read(rx))\n', 0, "ok"),
 ("plain values and atoms are copied to run", 'fn w(n: Int, a: Atom[Int]) Unit:\n  _ = reset(a, n)\n\nn = 5\na = Atom[Int](0)\n_ = run w(n, a)\n_ = run w(n, a)\nprintln(n)\n', 0, "ok"),
 ("run in a loop with an outer resource is refused", 'fn w(out: ChanW[Int]) Unit:\n  _ = write(out, 1)\n\nrx, tx = Chan[Int][2]()\nfor i in 1..=2:\n  _ = run w(tx)\n', 1, "handed to the new fiber inside a loop"),
 ("an inline fiber takes the resources it names", 'rx, tx = Chan[Int][2]()\n_ = run fn (tx):\n  _ = write(tx, 1)\n_ = write(tx, 2)\n', 1, "use of moved value `tx`"),
 ("closing twice is a compile error", 'init:\n  c = spawn("true")?\n  close(c)\n  close(c)\n', 1, "use of moved value `c`"),
 ("using a resource after closing it is a compile error", 'init:\n  c = spawn("true")?\n  close(c)\n  println(wait_child(c))\n', 1, "use of moved value `c`"),
 ("c.close() ends it too", 'init:\n  c = spawn("true")?\n  c.close()\n  c.close()\n', 1, "use of moved value `c`"),
 ("closing an outer resource in a loop is refused", 'init:\n  c = spawn("true")?\n  for i in 1..=2:\n    close(c)\n', 1, "closed inside a loop"),
 ("closing then leaving the loop is fine", 'init:\n  c = spawn("true")?\n  while:\n    close(c)\n    break\n', 0, "ok"),
 ("closing in both branches ends it", 'init:\n  c = spawn("true")?\n  if true:\n    close(c)\n  else:\n    close(c)\n  close(c)\n', 1, "use of moved value `c`"),
 ("a resource made in the loop may be closed in it", 'init:\n  for i in 1..=2:\n    c = spawn("true")?\n    close(c)\n', 0, "ok"),
 ("a function with several clauses is checked", 'fn f(c: Child, 0) Unit:\n  close(c)\nfn f(c: Child, n: Int) Unit:\n  _ = wait_child(c)\n\ninit:\n  c = spawn("true")?\n  f(c, 0)\n', 1, "takes ownership of `c`"),
 ("several clauses with move is fine", 'fn f(c: Child, 0) Unit:\n  close(c)\nfn f(c: Child, n: Int) Unit:\n  _ = wait_child(c)\n\ninit:\n  c = spawn("true")?\n  f(move c, 0)\n', 0, "ok"),
 ("a free function called as c.f() takes the receiver", 'fn eat(c: Child) Unit:\n  close(c)\n\ninit:\n  c = spawn("true")?\n  c.eat()\n  c.eat()\n', 1, "use of moved value `c`"),
 ("a borrowing function called as c.f() leaves it", 'fn look(c: Child) Int:\n  0\n\ninit:\n  c = spawn("true")?\n  println(c.look())\n  println(c.look())\n  close(c)\n', 0, "ok"),
 ("a tuple that holds a resource is a resource", 'tuple Conn:\n  io: Io\n\ninit:\n  f = open_file("x", ReadOnly)?\n  c = Conn(io: move f)\n  d = c\n', 1, "`c` is a resource; write `move c`"),
 ("a resource must be moved into a tuple", 'tuple Conn:\n  io: Io\n\ninit:\n  f = open_file("x", ReadOnly)?\n  c = Conn(io: f)\n', 1, "write `move f` to put it in a `Conn`"),
 ("moved into a tuple is fine", 'tuple Conn:\n  io: Io\n\ninit:\n  f = open_file("x", ReadOnly)?\n  c = Conn(io: move f)\n  close(c.io)\n', 0, "ok"),
 ("a function that closes a field takes the tuple", 'tuple Conn:\n  io: Io\n\nfn done(c: Conn) Unit:\n  close(c.io)\n\ninit:\n  f = open_file("x", ReadOnly)?\n  c = Conn(io: move f)\n  done(c)\n', 1, "`done` takes ownership of `c`"),
 ("a method that closes a field takes self", 'tuple Job:\n  c: Child\n\nimpl Job:\n  fn finish(self) Unit:\n    close(self.c)\n\ninit:\n  j = Job(c: move spawn("true")?)\n  j.finish()\n  j.finish()\n', 1, "use of moved value `j`"),
 ("a method that only looks leaves it", 'tuple Job:\n  c: Child\n\nimpl Job:\n  fn peek(self) Int:\n    0\n\ninit:\n  j = Job(c: move spawn("true")?)\n  println(j.peek())\n  println(j.peek())\n  close(j.c)\n', 0, "ok"),
 ("a function that returns a resource makes one", 'fn open_it() Child:\n  spawn("true")?\n\ninit:\n  c = open_it()\n  d = c\n', 1, "`c` is a resource"),
 ("a Result of a resource, unwrapped, is a resource", 'fn open_it() Result[Child, Error]:\n  spawn("true")\n\ninit:\n  c = open_it()?\n  d = c\n', 1, "`c` is a resource"),
 ("a value that is not a resource is not touched", 'fn f(n: Int) Int:\n  n\n\ninit:\n  x = 1\n  println(f(x))\n  println(f(x))\n', 0, "ok"),
]
fails = []
for name, src, rc_want, *wants in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "check", f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    o = r.stdout.decode() + r.stderr.decode()
    ok = r.returncode == rc_want and all(w in o for w in wants)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {r.returncode}) {o[:300]!r}"))
    if not ok: fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
