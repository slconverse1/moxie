"""`break(value)` needs a loop `else` that gives the value when the loop ends without a break (Spec, Loop values).
Run: python3 tests/run_loopelse.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
OK = [
 ("for with an else", 'xs = List(4, 8, 15, 16)\nfound = for x in xs\n  if x > 10\n    break(x)\nelse\n  -1\nprintln("$found")\n', "15\n"),
 ("for that runs out", 'xs = List(1, 2)\nfound = for x in xs\n  if x > 10\n    break(x)\nelse\n  -1\nprintln("$found")\n', "-1\n"),
 ("while with an else", 'n = 0\nr = while n < 10\n  if n * n > 30\n    break(n)\n  n = n + 1\nelse\n  -1\nprintln("$r")\n', "6\n"),
 ("a bare break needs no else", 'for x in List(1, 2, 3)\n  if x == 2\n    break\n  println("$x")\n', "1\n"),
 ("a labeled do gives a value without else", 'xs = List(4, 8, 15)\nfound = #search do\n  for x in xs\n    if x > 10\n      break #search(x)\n  -1\nprintln("$found")\n', "15\n"),
 ("an inner loop with its own else", 'rows = List(List(1, 20), List(3, 4))\nfor row in rows\n  big = for c in row\n    if c > 10\n      break(c)\n  else\n    0\n  println("$big")\n', "20\n0\n"),
 ("a labeled break out of the outer loop, with else", 'rows = List(List(1, 2), List(3, 40))\nr = #outer for row in rows\n  for c in row\n    if c > 10\n      break #outer(c)\nelse\n  -1\nprintln("$r")\n', "40\n"),
]
ERR = [
 ("no else", 'xs = List(4, 8, 15)\nfound = for x in xs\n  if x > 10\n    break(x)\nprintln("$found")\n', "needs an `else`"),
 ("the else belongs to the if", 'xs = List(4, 8, 15)\nfound = for x in xs\n  if x > 10\n    break(x)\n  else\n    -1\nprintln("$found")\n', "needs an `else`"),
 ("a while with no else", 'n = 0\nr = while n < 10\n  if n > 5\n    break(n)\n  n = n + 1\nprintln("$r")\n', "needs an `else`"),
 ("a labeled break to a loop with no else", 'rows = List(List(1, 2), List(3, 40))\nr = #outer for row in rows\n  for c in row\n    if c > 10\n      break #outer(c)\nprintln("$r")\n', "needs an `else`"),
]
fails = []
for name, src, want in OK:
    rc, out = run(src)
    good = rc == 0 and out == want
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:200]!r}"))
    if not good:
        fails.append(name)
for name, src, word in ERR:
    rc, out = run(src, "check")
    good = rc != 0 and word in out
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:200]!r}"))
    if not good:
        fails.append(name)
sys.exit(1 if fails else 0)
