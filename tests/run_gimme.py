"""`name@N` (outer bindings) in loops and blocks.  Run: python3 tests/run_gimme.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ("name@1 updates names bound before a loop", 'total = 0\ncount = 0\nfor score in List(70, 85, 90)\n  total@1 += score\n  count@1 += 1\nprintln("$total $count")\n', 0, "245 3"),
 ("reduce carries the state with no outer write", 'total = List(70, 85, 90) |> reduce(0, (acc, s) -> acc + s)\nprintln(total)\n', 0, "245"),
 ("a plain rebinding in a loop is an error", 'total = 0\nfor s in List(1, 2, 3)\n  total += s\nprintln(total)\n', 2, "reads the outer `total`"),
 ("name@N in a nested if", 'n = 1\nif true\n  n = 2\n  n@1 = 10\n  println("${n} ${n@1}")\nprintln("$n")\n', 0, "2 10\n10"),
 ("name@N with nothing to reach is an error", 'fn f() Int\n  x@1 = 5\n  1\nprintln(f())\n', 2, "no enclosing block binds"),
 ("a read in an expression", 'n = 5\nif true\n  n = 7\n  println(n@1 + n)\n', 0, "12"),
 ("the second layer out", 'n = 1\nif true\n  n = 2\n  if true\n    n = 3\n    println("${n} ${n@1} ${n@2}")\n', 0, "3 2 1"),
 ("the old spelling points to the new one", 'x = 1\nif true\n  x = 2\n  println(gimme.1.x)\n', 2, "x@1"),
 ("a field name after the number still works", 'tuple P deriving show\n  a Int\np = P(a: 4)\nif true\n  p = P(a: 9)\n  println(p@1.a + p.a)\n', 0, "13"),
 ("a function keeps its own total and updates the outer one", 'fn tally(scores List[Int]) Int\n  total = 0\n  for s in scores\n    total = s * 2\n    total@1 += total\n  total\nprintln(tally(List(1, 2, 3)))\n', 0, "12"),
 ("a function is a boundary for a module-level name", 'rate = 3\nfn bump() Int\n  rate@1 = 4\n  rate\nprintln(bump())\n', 2, "no enclosing block binds `rate`"),
 ("a closure is a boundary", 'fn f() Int\n  x = 1\n  g = () -> x@1\n  g()\nprintln(f())\n', 2, "no enclosing block binds `x`"),
 ("a function reads a module-level name without @", 'rate = 3\nfn price(n Int) Int\n  n * rate\nprintln(price(5))\n', 0, "15"),
 ("a label names the scope", 'total = 0\n#serve for x in List(1, 2, 3)\n  if x > 0\n    total@serve += x\nprintln(total)\n', 0, "6"),
 ("a label reaches past a shadow", 'total = 100\n#outer for i in List(1, 2)\n  total = 5\n  for j in List(1, 2)\n    total@outer += j\n    total@1 += 10\n    println("${total} ${total@outer}")\nprintln(total)\n', 0, "106"),
 ("a label on a while loop", 'count = 0\n#w for count < 3\n  count@w += 1\nprintln(count)\n', 0, "3"),
 ("an unknown label is an error", 'total = 0\nfor x in List(1)\n  total@nope += x\nprintln(total)\n', 2, "no enclosing loop or `do` is labeled `#nope`"),
 ("a label with nothing outside it", '#serve for x in List(1)\n  y@serve = 1\n', 2, "no enclosing block binds `y`"),
 ("an as-pattern is not a label", 'tuple P deriving show\n  a Int\n  b Int\nq = P(a: 1, b: 2)\nr@P(a, b) = q\nprintln("${r} ${a}")\n', 0, "P(a: 1, b: 2) 1"),
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
        ok = (r.returncode == rc_want or (rc_want == 2 and r.returncode != 0)) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:200]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
