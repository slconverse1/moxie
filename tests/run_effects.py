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
 ("pure fn that is pure", "pure fn f(x: Int) Int: x + 1\n", True, ""),
 ("pure fn that prints", 'pure fn f(x: Int) Int:\n  println("a")\n  x\n', False, "prints"),
 ("effect through a callee", 'fn g(): println("a")\npure fn f(x: Int) Int:\n  g()\n  x\n', False, "prints"),
 ("effect through recursion", 'fn g(n: Int) Unit:\n  if n == 0: println("a") else: g(n - 1)\npure fn f(): g(3)\n', False, "prints"),
 ("parameter call takes the argument's effect (pure)", "fn twice(f, x): f(f(x))\npure fn h(x: Int) Int: twice(_ + 1, x)\n", True, ""),
 ("parameter call takes the argument's effect (prints)", 'fn twice(f, x): f(f(x))\npure fn h(x: Int) Int: twice(fn (y): y + len(show(println("a"))), x)\n', False, "prints"),
 ("swap function may not park", "c = Atom[Int](0)\nch = Chan[Int](1)\nswap(c, fn (n): n + read(ch))\n", False, "swap"),
 ("swap function that is pure", "c = Atom[Int](0)\nswap(c, _ + 1)\n", True, ""),
 ("debug_assert condition must be pure", 'fn p(): println("x")\ndebug_assert(p() == ())\n', False, "debug_assert"),
 ("dbg is exempt", "pure fn f(x: Int) Int: dbg(x)\n", True, ""),
 ("read[T] parses and does not park", 'pure fn f(s: String): read[Int](s)\n', True, ""),
 ("contract conditions must be pure", 'fn f(x: Int) Int:\n  requires println("a") == ()\n  x\n', False, "must be pure"),
 ("declared prints, does print", 'prints fn f(s: String) Unit: println(s)\n', True, ""),
 ("declared prints through a callee (no propagation needed in callers)", 'fn g(s: String) Unit: println(s)\nprints fn f(s: String) Unit: g(s)\nfn h(): f("x")\nh()\n', True, ""),
 ("undeclared extra effect", 'prints fn f() Unit:\n  ch = Chan[Int](1)\n  println("a")\n  read(ch)\n', False, "not declared parks"),
 ("stale declaration", 'prints fn f(x: Int) Int: x\n', False, "never does"),
 ("impure with no effect", 'impure fn f(x: Int) Int: x\n', False, "declared impure"),
 ("pure and impure together", 'pure prints fn f(x: Int) Int: x\n', False, "both pure and impure"),
 ("interface member bound allows an impl", 'interface L:\n  prints fn log(self, s: String) Unit\ntuple Q:\n  n: Int\nimpl L for Q:\n  fn log(self, s: String) Unit: println(s)\n', True, ""),
 ("impl exceeds the interface bound", 'interface L:\n  prints fn log(self, s: String) Unit\ntuple Q:\n  n: Int\nimpl L for Q:\n  fn log(self, s: String) Unit:\n    ch = Chan[Int](1)\n    read(ch)\n', False, "does not allow"),
 ("a pure fn calling a declared member is caught", 'interface L:\n  prints fn log(self, s: String) Unit\ntuple Q:\n  n: Int\nimpl L for Q:\n  fn log(self, s: String) Unit: println(s)\npure fn f(q: Q) Unit: q.log("x")\n', False, "prints"),
]
fails = []
for name, src, ok, word in CASES:
    rc, o = check(src)
    good = (rc == 0) if ok else (rc != 0 and word in o)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else "  -> " + o.strip()[:120]))
    if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
