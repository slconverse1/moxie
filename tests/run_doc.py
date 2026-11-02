"""Tests for `moxie doc`.  Run: python3 tests/run_doc.py"""
import io, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, "examples", "documented.mxi")


def run(*a):
    r = subprocess.run([sys.executable, "-m", "moxie", *a], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


fails = []
def chk(name, cond):
    print(("ok    " if cond else "FAIL  ") + name)
    if not cond: fails.append(name)

rc, out, err = run("doc", EX, "--check")
chk("check passes on documented example", rc == 0 and "4 examples ok" in out)
rc, out, err = run("doc", EX, "--format", "md")
chk("md has signature", "fn to_f(c: Int) Int" in out)
chk("md has contracts", "`requires c >= -273`" in out and "`invariant celsius >= -273`" in out)
chk("md has interface member contract", "`ensures len(result) > 0`" in out)
chk("md has module doc", "A tiny temperature library." in out)
rc, out, err = run("doc", EX)
chk("html default", out.startswith("<!doctype html>") and "<h3" in out)
src = open(EX).read().replace("/// 50", "/// 51").replace("[`to_f`]", "[`nope`]")
with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
    f.write(src)
rc, out, err = run("doc", f.name, "--check")
chk("failing example and broken link detected", rc == 1 and "example failed" in err and "broken link" in err)
os.unlink(f.name)
rc, out, err = run("test", EX)
chk("moxie test runs doctests", rc == 0 and "doctest to_f" in out)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
