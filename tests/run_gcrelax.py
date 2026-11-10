"""moxie/gc stores capturing closures anywhere; no-GC moxie still refuses.  Run: python3 tests/run_gcrelax.py"""
import subprocess, sys, os, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "tuple H:\n  f: (Int) -> Int\nfn make(k: Int) H:\n  H(f: (x): x + k)\nhs = List(make(1), make(2))\nprintln(hs(1).f(10))\nds = Dict(\"a\": (x): x * 3)\nprintln(ds(\"a\").unwrap()(4))\n"
CASES = [("moxie/gc stores a capturing closure", ["--gc"], "12\n12", None),
         ("no-GC moxie refuses it", [], None, "only plain functions can be stored")]
fails = []
f = os.path.join(tempfile.mkdtemp(), "t.mx")
open(f, "w").write(SRC)
for name, flags, out_has, err_has in CASES:
    r = subprocess.run([sys.executable, "-m", "moxie", "run", *flags, f], capture_output=True, text=True, cwd=ROOT, timeout=120)
    ok = (out_has is None or out_has in r.stdout) and (err_has is None or err_has in r.stdout + r.stderr) and "Traceback" not in r.stderr
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> {(r.stdout + r.stderr).strip()[-200:]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
