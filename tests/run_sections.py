"""Operator sections and placeholder lambdas are typed like the lambda they stand for.  Run: python3 tests/run_sections.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CASES = [
 ("(+ 1) on Strings", 'xs List[String] = List("a")\nys = xs.map((+ 1))\n', "cannot apply `+` to `String` and `Int`"),
 ("(* 2) on Strings", 'xs List[String] = List("a")\nys = xs.map((* 2))\n', "cannot apply `*` to `String` and `Int`"),
 ("_ + 1 on Strings", 'xs List[String] = List("a")\nys = xs.map(_ + 1)\n', "cannot apply `+` to `String` and `Int`"),
 ("(> \"x\") on Ints", 'ys = List(1, 2).filter((> "x"))\n', "cannot compare `Int` and `String`"),
 ("(and true) on Ints", 'ys = List(1, 2).filter((and true))\n', "`and` needs `Bool` operands"),
 ("(- 1) fits Ints", "ys = List(1, 2).map((- 1))\nprintln(ys)\n", None),
 ("(+ \"z\") fits Strings", 'ys = List("a").map((+ "z"))\nprintln(ys)\n', None),
 ("(* 2) fits Floats", "ys = List(1.5).map((* 2))\nprintln(ys)\n", None),
 ("(and true) fits Bools", "ys = List(true, false).filter((and true)).collect()\nprintln(ys)\n", None),
 ("(in allowed) fits", "allowed = Set(1, 2)\nys = List(1, 3).filter((in allowed)).collect()\nprintln(ys)\n", None),
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
