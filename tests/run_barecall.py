"""Bare calls (no parentheses): a plain name followed by an indented block is a call whose arguments are the indented lines.
Also at the right of `=`.  A callee with a `block` parameter takes the lines as its block of children.  Keywords that open
a block (`if`, `wait`, ...) never start a bare call.  Run: python3 tests/run_barecall.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AREA = 'fn area(w Int, h Int) Int\n  w * h\n\n'
SCALE = 'fn scale(x Int, k Int) Int\n  x * k\n\n'
LUNCH = 'fn lunch(block items List[String]) String\n  join(items, ", ")\n\n'

CASES = [
 ("statement with nested bare call", AREA + SCALE + 'println\n  area\n    scale\n      2\n      3\n    4\n', 0, "24"),
 ("bare call on the right of =", AREA + 'r = area\n  2\n  3\nprintln(r)\n', 0, "6"),
 ("nested bare call on the right of =", AREA + SCALE + 's = area\n  scale\n    2\n    3\n  4\nprintln(s)\n', 0, "24"),
 ("block parameter as a statement", LUNCH + 'println\n  lunch\n    "soup"\n    "bread"\n', 0, "soup, bread"),
 ("block parameter on the right of =", LUNCH + 'menu = lunch\n  "soup"\n  "bread"\nprintln(menu)\n', 0, "soup, bread"),
 ("if header still takes its body", 'ok = true\nif ok\n  println("yes")\n', 0, "yes"),
 ("wait block is not a call", 'wait\n  println("body")\n', 0, "body"),
 ("a zero-argument call keeps its parentheses in block form", 'fn two() Int\n  7\nprintln\n  two()\n', 0, "7"),
 ("a value followed by an indent is an error", 'x = 1\n  2\n', 2, "unexpected indent"),
]

fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = ((r.returncode != 0) if rc_want == 2 else r.returncode == 0) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:200]}"))
        if not ok:
            fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
