"""Operator sections: `(+ 1)`, `(10 -)`, `(- 1)` with a space, ``(`plus` 2)``.  Run: python3 tests/run_sections.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
PRE = 'fn plus(a Int, b Int) Int\n  a + b\n'
CASES = [
 ("in is a section", 'println(List(1, 2, 3, 4).filter((in List(2, 4))).collect())\n', 0, "List(2, 4)"),
 ("a left in section", 'println(List(List(1, 2), List(3)).map((2 in)).collect())\n', 0, "List(true, false)"),
 ("and and or are sections", 'println(List(true, false).map((and true)).collect())\nprintln(List(true, false).map((or false)).collect())\nprintln(List(true, false).map((true and)).collect())\n', 0, "List(true, false)"),
 ("a for header over a parenthesized value is not a section", 'for x in (List(1, 2))\n  println(x)\n', 0, "1\n2"),
 ("right section", 'println(List(1, 2, 3).map((+ 1)))\n', 0, "List(2, 3, 4)"),
 ("left section", 'println(List(1, 2, 3).map((10 -)))\n', 0, "List(9, 8, 7)"),
 ("right subtraction needs the space", 'println(List(1, 2, 3).map((- 1)))\n', 0, "List(0, 1, 2)"),
 ("no space is negation", 'println((-4))\nx = 7\nprintln((-x))\n', 0, "-7"),
 ("a space after the minus is a section", 'println((- 4)(10))\n', 0, "6"),
 ("multiplication and comparison", 'println(List(1, 2, 3).map((* 2)))\nprintln(List(1, 5, 3).filter((> 2)).collect())\n', 0, "List(5, 3)"),
 ("backtick sections", PRE + 'println(List(5, 6).map((`plus` 2)))\nprintln(List(5, 6).map((2 `plus`)))\n', 0, "List(7, 8)"),
 ("a section is a value", 'inc = (+ 1)\nprintln(inc(41))\n', 0, "42"),
 ("in a pipe", 'println(5 |> (* 3))\n', 0, "15"),
 ("a right operand that is an expression", 'k = 2\nprintln(List(1, 2).map((+ k * 3)))\n', 0, "List(7, 8)"),
 ("grouping and tuples are unchanged", 'println((1 + 2))\nprintln((1, 2))\nprintln((7))\n', 0, "(1, 2)"),
 ("a section has its hole already", 'println(List(1).map((+ _)))\n', 2, "already has its hole"),
 ("a left section has its hole already", 'println(List(1).map((_ -)))\n', 2, "already has its hole"),
]
fails = []
for name, src, want, word in CASES:
    for gc in (False, True):
        p = os.path.join(D, "t.mxi")
        open(p, "w").write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if want == 2 else "run", p], cwd=ROOT, capture_output=True, text=True)
        o = r.stdout + r.stderr
        good = ((r.returncode != 0) if want == 2 else (r.returncode == 0)) and word in o
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={r.returncode} {o.strip()[:300]!r}"))
        if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
