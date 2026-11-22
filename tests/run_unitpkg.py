"""Units across packages: a package's `export unit` declarations are in scope where it is imported.  Run: python3 tests/run_unitpkg.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHYS = """export unit m
export unit s
export unit km = 1000 m
export unit kmh = km / s
unit hidden

export fn speed(d Double[m], t Double[s]) Double[m/s] = d / t
export fn twice[U](x Double[U]) Double[U] = x + x
"""
MULTI = {"Moxie.toml": 'files = ["a.mxi", "b.mxi"]\n', "a.mxi": "export unit m\nexport unit s\n",
         "b.mxi": "export unit km = 1000 m\nexport fn dist(x Double[km]) Double[m] = x\nexport fn sp(d Double[m], t Double[s]) Double[m/s] = d / t\n"}
def run(main, gc=False):
    with tempfile.TemporaryDirectory() as d:
        if main.startswith("import multi"):
            os.mkdir(os.path.join(d, "multi"))
            for k, v in MULTI.items():
                open(os.path.join(d, "multi", k), "w").write(v)
        else:
            open(os.path.join(d, "phys.mxi"), "w").write(PHYS)
        p = os.path.join(d, "main.mxi")
        open(p, "w").write(main)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", p]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr
CASES = [
 ("an imported unit makes a quantity", "import phys\nprintln(phys.speed(10.0 m, 2.0 s))\n", "5.0"),
 ("an imported scaled unit is stored in its base", "import phys\nd = 2.5 km\nprintln(d + 500.0 m)\n", "3000.0"),
 ("in converts with an imported unit", "import phys\nprintln(phys.twice(3.0 km) in km)\n", "6.0"),
 ("a result keeps its unit", "import phys\nv Double[m/s] = phys.speed(10.0 m, 2.0 s)\nprintln(v)\n", "5.0"),
 ("a wrong result unit is an error", "import phys\nbad Double[s] = phys.speed(10.0 m, 2.0 s)\n", "expected `Double[s]`, found `Double[m/s]`"),
 ("a wrong argument unit is an error", "import phys\nb = phys.speed(10.0 s, 2.0 s)\n", "expected `Double[m]`, found `Double[s]`"),
 ("imported units still differ", "import phys\nc = 1.0 m + 2.0 s\n", "the units differ"),
 ("a unit-generic package function", "import phys\nx Double[m] = phys.twice(2.0 m)\nprintln(x)\n", "4.0"),
 ("an import list works too", "import phys(speed)\nprintln(speed(9.0 m, 3.0 s))\n", "3.0"),
 ("a unit not exported is not a literal", "import phys\nbad = 2.0 hidden\n", "syntax error"),
 ("units of a many-file package: one file uses another's unit", "import multi\nprintln(multi.dist(2.0 km))\n", "2000.0"),
 ("units of a many-file package: functions across files", "import multi\nprintln(multi.sp(10.0 m, 2.0 s))\n", "5.0"),
 ("units of a many-file package: a scaled unit converts", "import multi\nprintln(2.5 km in m)\n", "2500.0"),
 ("a local unit still works beside imported ones", "import phys\nunit kg\nw = 2.0 kg\nprintln(w * 2.0)\n", "4.0"),
]
fails = []
for name, src, want in CASES:
    for gc in (False, True):
        rc, out = run(src, gc)
        good = want in out
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
        if not good:
            fails.append(name)
print(f"{len(CASES) * 2 - len(fails)} of {len(CASES) * 2} passed")
sys.exit(1 if fails else 0)
