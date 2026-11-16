"""Anonymous fns have no `->`: `fn (params) Ret` with an indented body, bound first; a lambda is the only form that uses `->`.
Effects of a bound anonymous fn reach whoever calls it.  Run: python3 tests/run_anonfn.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ("block form runs", 'say = fn (s String) Unit\n  println(s)\nsay("hi")\n', 0, "hi"),
 ("result type is optional", 'twice = fn (n Int)\n  println(n * 2)\ntwice(4)\n', 0, "8"),
 ("an arrow after fn is an error", 'say = fn (s String) Unit -> println(s)\n', 2, "has no `->`"),
 ("an arrow before an inline fiber body is an error", 'rx, tx = Chan[Int][1]()\n\\run fn (tx) ->\n  \\write(tx, 1)\n', 2, "has no `->`"),
 ("inline fiber with a block", 'rx, tx = Chan[Int][1]()\n\\run fn (tx)\n  \\write(tx, 5)\nprintln(read(rx))\n', 0, "Ok(5)"),
 ("an inline body can't sit inside a call", 'fn twice(f () -> Unit) Unit\n  f()\ntwice(fn ()\n  println("x"))\n', 2, "bind it on its own line first"),
 ("a lambda may not print", 'f = (x Int) -> println(x)\n', 2, "must be pure"),
 ("a bound anon fn's effect reaches a pure fn", 'pure fn f() Int\n  r = fn () Result[String, Error]\n    read_line()\n  \\r()\n  1\n', 2, "parks"),
 ("an uncalled bound anon fn adds no effect", 'pure fn f() Int\n  r = fn () Unit\n    println("x")\n  1\nprintln(f())\n', 0, "1"),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = ((r.returncode != 0) if rc_want == 2 else r.returncode == 0) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:200]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
