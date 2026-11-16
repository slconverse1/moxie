"""`moxie doc` lists the functions marked `unsafe` or `dynamic`.  Run: python3 tests/run_docmarks.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '/// Reads a field.\ndynamic fn read_name(d Dyn) String\n  "x"\n\n/// Plain.\nexport fn plain(n Int) Int\n  n\n'
fails = []
with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "m.mxi")
    open(f, "w").write(SRC)
    for fmt, key in (("md", "index.md"), ("html", "index.html")):
        out = os.path.join(d, "out_" + fmt)
        r = subprocess.run([sys.executable, "-m", "moxie", "doc", f, "-o", out, "--private", "--format", fmt], cwd=ROOT, capture_output=True, text=True)
        text = open(os.path.join(out, key)).read() if os.path.exists(os.path.join(out, key)) else r.stdout + r.stderr
        for want in ("Marked functions", "read_name", "dynamic"):
            ok = want in text
            print(("ok    " if ok else "FAIL  ") + f"{fmt}: has {want!r}")
            if not ok: fails.append((fmt, want))
        ok = "plain</code>" not in text.split("Marked functions")[1].split("<h3")[0].split("### fn")[0] if "Marked functions" in text else False
        print(("ok    " if ok else "FAIL  ") + f"{fmt}: an unmarked function is not in the marked list")
        if not ok: fails.append((fmt, "unmarked"))
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
