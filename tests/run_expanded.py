"""Expanded form: inside `( ... )`, one item per line with no commas (parameters and arguments).
A line break ends an item when the item is complete and the next line starts a new one.
A line starting with `-` followed by a space continues the line above; `-b` starts a new item.
Commas are not allowed in a call or parameter list that runs over several lines
(the strict form, one line with commas, is unchanged).  Run: python3 tests/run_expanded.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AREA = 'fn area(\n  w Int\n  h Int\n) Int\n  w * h\n'
PAIR = 'fn pair(\n  a Int\n  b Int\n) Int\n  a * 10 + b\n'
ONE = 'fn one(x Int) Int\n  x\n'

CASES = [
 ("expanded parameters", AREA + 'println(area(2, 3))\n', 0, "6"),
 ("expanded arguments", AREA + 'println(area(\n  2\n  3\n))\n', 0, "6"),
 ("expanded keyword arguments", AREA + 'println(area(\n  w: 2\n  h: 3\n))\n', 0, "6"),
 ("compact form over several lines is an error", AREA + 'println(area(2,\n  3))\n', 2, "one item per line"),
 ("trailing comma with expanded items is an error", AREA + 'println(area(\n  2,\n  3,\n))\n', 2, "one item per line"),
 ("a leading - with a space continues the line", ONE + 'println(one(\n  10 - 4\n))\n', 0, "6"),
 ("a leading -b starts a new item (negation)", PAIR + 'println(pair(\n  1\n  -4\n))\n', 0, "6"),
 ("one item per line, last item before )", PAIR + 'println(pair(\n  1\n  2\n))\n', 0, "12"),
 ("two items on one line are an error", PAIR + 'println(pair(\n  1\n  2 3\n))\n', 2, "expected ')'"),
 ("open tuple in generics, expanded", 'fn f[R (\n  a Int\n  ...\n)](r R) R = r.update\n  a: 2\nprintln(f((a: 1)))\n', 0, "(a: 2)"),
 ("an inline body can't sit inside a call", 'fn twice(f () -> Unit) Unit\n  f()\ntwice(fn ()\n  println("x"))\n', 2, "bind it on its own line first"),
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
        if not ok:
            fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
