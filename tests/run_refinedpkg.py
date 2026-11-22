"""Refined aliases across packages (`export type Pos = Int where self > 0`).  Run: python3 tests/run_refinedpkg.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
LIB = "export type Pos = Int where self > 0\nexport fn half(n Int) Int = n / 2\n"
CASES = [
 ("a qualified alias as a parameter, proved", "import lib\nfn twice(n lib.Pos) Int = n * 2\nprintln(twice(4))\n", 0, "8"),
 ("a literal that breaks the condition", "import lib\nfn twice(n lib.Pos) Int = n * 2\nprintln(twice(0))\n", 1, ""),
 ("an unproved argument is an error", "import lib\nfn twice(n lib.Pos) Int = n * 2\nfn begin(k Int) Int = twice(k)\nprintln(begin(3))\n", 2, "can't"),
 ("a from-import used unqualified", "import lib(Pos)\nfn twice(n Pos) Int = n * 2\nprintln(twice(5))\n", 0, "10"),
 ("a refined binding", "import lib\nx lib.Pos = 3\nprintln(x)\n", 0, "3"),
 ("a refined binding that fails", "import lib\nx lib.Pos = 0 - 3\nprintln(x)\n", 1, ""),
 ("a refined field", "import lib\ntuple Box deriving show\n  n lib.Pos\nprintln(Box(n: 2).n)\n", 0, "2"),
 ("a refined field that fails", "import lib\ntuple Box deriving show\n  n lib.Pos\nprintln(Box(n: 0).n)\n", 1, ""),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "lib.mxi"), "w").write(LIB)
            open(os.path.join(d, "main.mxi"), "w").write(src)
            cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["--prove"] + ["check" if rc_want == 2 else "run", os.path.join(d, "main.mxi")]
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        o = (r.stdout + r.stderr).strip()
        ok = ((r.returncode != 0) if rc_want else r.returncode == 0) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o[:260]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
