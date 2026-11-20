"""`;` separates statements on a line only at the start of a line: never in a lambda, an arm, or after `then`, `do` or `else`.
Run: python3 tests/run_semicolon.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
    ("two bindings on a line", 'a = 1; b = 2\nprintln(a + b)\n', 0, "3"),
    ("in a function body", 'fn f(v Int) Int\n  w = v * 2; w + 1\nprintln(f(4))\n', 0, "9"),
    ("trailing semicolon", 'a = 1;\nprintln(a)\n', 0, "1"),
    ("multi-array still works", 'm = (1, 2; 3, 4)\nprintln(m)\n', 0, "MultiArray(1, 2, 3, 4)"),
    ("not after then", 'x = 2\nif x > 1 then println("a"); println("b")\n', 1, "unexpected ';'"),
    ("not after do", 'while false do println("a"); println("b")\n', 1, "unexpected ';'"),
    ("not in a lambda", 'f = (x) -> y = x + 1; y * 2\nprintln(f(3))\n', 1, "undefined name"),
    ("not in a when arm", 'n = 1\nwhen n\n  1 -> println("one"); println("uno")\n  _ -> println("x")\n', 1, "';'"),
]
bad = 0
for name, src, want_rc, want in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    out = (r.stdout + r.stderr).decode()
    ok = (r.returncode == 0) == (want_rc == 0) and want in out
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else "  " + repr(out[-160:])))
    bad += not ok
print(f"{bad} failed")
sys.exit(1 if bad else 0)
