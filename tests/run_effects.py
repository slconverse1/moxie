"""Effect inference tests.  Run: python3 tests/run_effects.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check(src):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "check", f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr

CASES = [
 ("pure fn that is pure", 'pure fn f(x Int) Int = x + 1\n', True, ""),
 ("pure fn that prints", 'pure fn f(x Int) Int\n  println("a")\n  x\n', False, "prints"),
 ("effect through a callee", 'fn g() Unit = println("a")\npure fn f(x Int) Int\n  g()\n  x\n', False, "prints"),
 ("effect through recursion", 'fn g(n Int) Unit\n  if n == 0 then println("a") else g(n - 1)\npure fn f() Unit = g(3)\n', False, "prints"),
 ("parameter call takes the argument's effect (pure)", 'fn twice(f (Int) -> Int, x Int) Int = f(f(x))\npure fn h(x Int) Int = twice(_ + 1, x)\n', True, ""),
 ("parameter call takes the argument's effect (prints)", 'fn twice(f (Int) -> Int, x Int) Int = f(f(x))\npure fn h(x Int) Int = twice((y) -> y + len(show(println("a"))), x)\n', False, "prints"),
 ("pure fn may not create a channel", 'pure fn f() Int\n  rx, tx = Chan[Int][1]()\n  1\n', False, "uses a resource"),
 ("pure fn may not create an atom", 'pure fn f() Int\n  a = Atom(1)\n  1\n', False, "uses a resource"),
 ("pure fn may not read an atom", 'fn g(a Atom[Int]) Int = @a\npure fn f(a Atom[Int]) Int\n  g(a)\n', False, "uses a resource"),
 ("pure fn may not change an atom", 'pure fn f(a Atom[Int]) Int\n  reset(a, 0)\n  1\n', False, "uses a resource"),
 ("pure fn may not arm a timer", 'pure fn f(t Timer) Int\n  arm(t, 1s)\n  1\n', False, "uses a resource"),
 ("the resource effect travels through callees", 'fn make() Int\n  a = Atom(1)\n  1\npure fn f() Int\n  make()\n', False, "uses a resource"),
 ("a function declared impure may use a resource", 'impure fn f() Int\n  a = Atom(1)\n  1\n', True, ""),
 ("a function declared parks must say impure to use a resource", 'parks fn f(rx ChanR[Int]) Int\n  a = Atom(1)\n  read(rx)\n  1\n', False, "must be declared impure"),
 ("an undeclared function may use a resource", 'fn f() Int\n  a = Atom(1)\n  1\n', True, ""),
 ("a forall body must stay free of resources", 'forall x Int\n  a = Atom(x)\n  assert(true)\n', False, "uses a resource"),
 ("swap function may not park", 'c = Atom[Int](0)\nch = Chan[Int](1)\nswap(c, (n) -> n + read(ch))\n', False, "swap"),
 ("swap function that is pure", "c = Atom[Int](0)\nswap(c, _ + 1)\n", True, ""),
 ("debug_assert condition must be pure", 'fn p() Unit = println("x")\ndebug_assert(p() == ())\n', False, "debug_assert"),
 ("dbg is exempt", 'pure fn f(x Int) Int = dbg(x)\n', True, ""),
 ("trace is exempt", 'pure fn f(x Int) Int\n  trace("in f")\n  x\n', True, ""),
 ("read[T] parses and does not park", 'pure fn f(s String) Result[Int, Error] = read[Int](s)\n', True, ""),
 ("contract conditions must be pure", 'fn f(x Int) Int\n  requires println("a") == ()\n  x\n', False, "must be pure"),
 ("declared prints, does print", 'prints fn f(s String) Unit = println(s)\n', True, ""),
 ("declared prints through a callee (no propagation needed in callers)", 'fn g(s String) Unit = println(s)\nprints fn f(s String) Unit = g(s)\nfn h() Unit = f("x")\nh()\n', True, ""),
 ("undeclared extra effect", 'prints fn f() Unit\n  ch = Chan[Int](1)\n  println("a")\n  read(ch)\n', False, "not declared parks"),
 ("stale declaration", 'prints fn f(x Int) Int = x\n', False, "never does"),
 ("impure with no effect", 'impure fn f(x Int) Int = x\n', False, "declared impure"),
 ("pure and impure together", 'pure prints fn f(x Int) Int = x\n', False, "both pure and impure"),
 ("interface member bound allows an impl", 'interface L\n  prints fn log(self, s String) Unit\ntuple Q\n  n Int\nimpl L for Q\n  fn log(self, s String) Unit = println(s)\n', True, ""),
 ("impl exceeds the interface bound", 'interface L\n  prints fn log(self, s String) Unit\ntuple Q\n  n Int\nimpl L for Q\n  fn log(self, s String) Unit\n    ch = Chan[Int](1)\n    read(ch)\n', False, "does not allow"),
 ("a pure fn calling a declared member is caught", 'interface L\n  prints fn log(self, s String) Unit\ntuple Q\n  n Int\nimpl L for Q\n  fn log(self, s String) Unit = println(s)\npure fn f(q Q) Unit = q.log("x")\n', False, "prints"),
]
fails = []
for name, src, ok, word in CASES:
    rc, o = check(src)
    good = (rc == 0) if ok else (rc != 0 and word in o)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else "  -> " + o.strip()[:120]))
    if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
