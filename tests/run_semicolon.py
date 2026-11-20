"""`;` joins statements in a one-line lambda body or a `when`/`select` arm body.  Not after `then`, `do` or `else` of an `if`.
Run: python3 tests/run_semicolon.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
    ("lambda", 'f = (x) -> y = x + 1; y * 2\nprintln(f(3))\n', 0, "8"),
    ("lambda in a call", 'xs = List(1, 2, 3).map((v) -> w = v * v; w + 1) |> collect()\nprintln(xs)\n', 0, "List(2, 5, 10)"),
    ("when arm", 'fn s(n Int) String\n  when n\n    1 -> println("one"); "uno"\n    2 -> println("two"); println("dos"); "dos"\n    _ -> "other"\nprintln(s(1))\nprintln(s(2))\n', 0, "one\nuno\ntwo\ndos\ndos"),
    ("else arm", 'fn s(n Int) Int\n  when n\n    1 -> 10\n    else a = n * 2; a + 1\nprintln(s(5))\n', 0, "11"),
    ("select arm", 'rx, tx = Chan[Int][1]()\n_ = write(tx, 4)\nselect\n  x = read(rx) -> println(x); println(x + 1)\n\n  else println("none")\n', 0, "4\n5"),
    ("trailing semicolon", 'f = (x) -> y = x + 1; y;\nprintln(f(1))\n', 0, "2"),
    ("multi-array still works", 'm = (1, 2; 3, 4)\nprintln(m)\n', 0, "MultiArray(1, 2, 3, 4)"),
    ("not after then", 'x = 2\nif x > 1 then println("a"); println("b")\n', 1, "unexpected ';'"),
    ("not after do", 'while false do println("a"); println("b")\n', 1, "unexpected ';'"),
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
