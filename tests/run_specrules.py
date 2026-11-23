"""Rules the Spec states as errors or aborts, found unenforced by an audit of its claims.  Run: python3 tests/run_specrules.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def moxie(src, cmd="check"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False, encoding="utf-8") as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
fails = []
def chk(name, cond):
    print(("ok    " if cond else "FAIL  ") + name)
    if not cond: fails.append(name)
def rejects(name, src, msg, cmd="check"):
    rc, o = moxie(src, cmd)
    chk(name, rc != 0 and msg in o)
def accepts(name, src):
    rc, o = moxie(src)
    chk(name, rc == 0)

rejects("a bare _ mixed with _2 is an error", "println(List(1, 2, 3) |> reduce(0, _1 + _2 + _))\n", "can't be mixed")
accepts("_ and _1 name the one parameter", "println(List(1, 2) |> map(_ + _1) |> collect())\n")
accepts("numbered placeholders", "println(List(1, 2, 3) |> reduce(0, _1 + _2))\n")
rejects("x = 5 if c", "c = true\nx = 5 if c\n", "trailing `if`")
rejects("Python's conditional points to if-then-else", "c = true\nx = 1 if c else 2\n", "if c then a else b")
accepts("a trailing if on a call", "c = true\nprintln(1) if c\n")
rejects("a cut inside a literal's character (compile time)", "println(\"é\"(0..<1))\n", "multi-byte")
rejects("a cut inside a character aborts", "s = \"éx\"\nn = len(s) - 2\nprintln(s(0..<n))\n", "multi-byte", "run")
accepts("a cut between characters", "println(\"éx\"(0..<2))\n")
rejects("regex.must aborts on a bad pattern", "import regex\nr = regex.must(\"a(\")\nprintln(1)\n", "unwrap of an Err", "run")
rejects("a field called on a constructed value", "tuple P\n  x Int\nprintln(P(x: 1).x(2))\n", "not a function")
rejects("a field called on a call result", "tuple P\n  x Int\nfn mk() P = P(x: 1)\nprintln(mk().x(2))\n", "not a function")
accepts("a method called on a constructed value", "tuple P deriving show\n  x Int\nimpl P\n  fn dbl(self) Int = self.x * 2\nprintln(P(x: 1).dbl())\n")
rejects("forward fn and definition differ in type parameters", "forward fn f(n Int) Bool\nfn f[T](n Int) Bool = true\nprintln(f(1))\n", "type parameter")
accepts("forward fn with matching type parameters", "forward fn f[T](n T) Bool\nfn f[T](n T) Bool = true\nprintln(f(1))\n")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
