"""`for COND` is a loop on a condition, as in Go, and `for` is the only loop: `while` is a syntax error.  Run: python3 tests/run_forcond.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ("for on a counter", "n = 0\nfor n < 3\n  n = n + 1\n  println(n)\n", "", 0, "1\n2\n3"),
 ("for on an end-of-file test", "for read_line() is Ok(line)\n  println(\"got ${line}\")\n", "a\nb\n", 0, "got a\ngot b"),
 ("for true runs until a break", "for true\n  println(1)\n  break\n", "", 0, "1"),
 ("while is refused", "n = 0\nwhile n < 3\n  n = n + 1\n", "", 2, None),
 ("for x in xs is still iteration", "for x in List(7, 8)\n  println(x)\n", "", 0, "7\n8"),
 ("break and continue in a condition loop", "n = 0\nfor n < 10\n  n = n + 1\n  continue if n == 2\n  break if n > 4\n  println(n)\n", "", 0, "1\n3\n4"),
 ("a bracketed in does not make it iteration", "n = 0\nfor (n < 2)\n  n = n + 1\n  println(n)\n", "", 0, "1\n2"),
 ("a membership test as a condition is bracketed", "xs = Set(1, 2)\nn = 1\nfor (n in xs)\n  println(n)\n  n = n + 1\n", "", 0, "1\n2"),
 ("an else on a condition loop", "n = 0\nx = for n < 2\n  n = n + 1\nelse\n  n\nprintln(x)\n", "", 0, "2"),
]
fails = []
for name, src, stdin, rc, want in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["--allow-stdin", "run", f.name], cwd=ROOT, input=stdin, capture_output=True, text=True)
        os.unlink(f.name)
        o = (r.stdout + r.stderr).strip()
        ok = r.returncode == rc and (o == want if want is not None else "write `for`" in o)
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o[:240]!r}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
