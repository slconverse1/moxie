"""`readonly String` is the type of a string that lives for the whole program; `static String` is an error that says so.  Run: python3 tests/run_readonly.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ("readonly String parameter", 'fn show(msg readonly String) Unit\n  println(msg)\nshow("hi")\n', 0, "hi"),
 ("readonly String field", 'tuple Tag deriving show\n  label readonly String\nprintln(Tag(label: "a"))\n', 0, 'Tag(label: "a")'),
 ("static String is an error", 'fn show(msg static String) Unit\n  println(msg)\n', 2, "readonly String"),
 ("static fn still works", 'tuple Pt deriving show\n  x Int\nimpl Pt\n  static fn origin() Pt = Pt(x: 0)\nprintln(Pt.origin())\n', 0, "Pt(x: 0)"),
]
fails = []
for name, src, rc, want in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    o = (r.stdout + r.stderr).strip()
    ok = (r.returncode == 0 and o == want) if rc == 0 else (r.returncode != 0 and want in o)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> rc={r.returncode} {o[:240]}"))
    if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
