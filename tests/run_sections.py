"""Operator sections and placeholder lambdas are typed like the lambda they stand for.  Run: python3 tests/run_sections.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CASES = [
 ("_ + 1 on Strings", 'xs List[String] = List("a")\nys = xs.map(_ + 1)\n', "cannot apply `+` to `String` and `Int`"),
 ("_ * 2 on Strings", 'xs List[String] = List("a")\nys = xs.map(_ * 2)\n', "cannot apply `*` to `String` and `Int`"),
 ("_ > \"x\" on Ints", 'ys = List(1, 2).filter(_ > "x")\n', "cannot compare `Int` and `String`"),
 ("_ and true on Ints", 'ys = List(1, 2).filter(_ and true)\n', "`and` needs `Bool` operands"),
 ("_ - 1 fits Ints", "ys = List(1, 2).fmap(_ - 1)\nprintln(ys)\n", None),
 ("_ + \"z\" fits Strings", 'ys = List("a").fmap(_ + "z")\nprintln(ys)\n', None),
 ("_ * 2 fits Floats", "ys = List(1.5).fmap(_ * 2)\nprintln(ys)\n", None),
 ("_ and true fits Bools", "ys = List(true, false).filter(_ and true).collect()\nprintln(ys)\n", None),
 ("_ in allowed fits", "allowed = Set(1, 2)\nys = List(1, 3).filter(_ in allowed).collect()\nprintln(ys)\n", None),
 ("10 - _ fits Ints", "ys = List(1, 2).fmap(10 - _)\nprintln(ys)\n", None),
 ("(+ 1) is not a function", 'ys = List(1, 2).map((+ 1))\n', "an operator on its own is not a function"),
 ("(10 -) is not a function", 'ys = List(1, 2).map((10 -))\n', "an operator on its own is not a function"),
 ("(in allowed) is not a function", 'allowed = Set(1)\nys = List(1, 3).filter((in allowed))\n', "an operator on its own is not a function"),
 ("(- 4) with a space is not a function", 'ys = List(1).map((- 4))\n', "an operator on its own is not a function"),
 ("(-4) is negation", "println((-4))\n", None),
]
fails = []
for name, src, word in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check", f.name], cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = (r.returncode != 0 and word in o) if word else r.returncode == 0
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
