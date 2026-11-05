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
