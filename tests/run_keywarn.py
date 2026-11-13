"""The Dict key / Set element size warning.  Run: python3 tests/run_keywarn.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []

def check(src, manifest=None):
    d = tempfile.mkdtemp(prefix="mxkw")
    open(os.path.join(d, "main.mxi"), "w").write(src)
    if manifest:
        open(os.path.join(d, "Moxie.toml"), "w").write(manifest)
    r = subprocess.run([sys.executable, "-m", "moxie", "check"], cwd=d, env=dict(os.environ, PYTHONPATH=ROOT), capture_output=True, timeout=60)
    return r.returncode, r.stdout.decode() + r.stderr.decode()

def chk(name, src, want_warn, manifest=None, *extra):
    rc, out = check(src, manifest)
    warned = "warning size" in out
    ok = warned == want_warn and all(e in out for e in extra)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
    if not ok: fails.append(name)

TYPES = 'tuple Big\n  a String[60]\n  b Int\ntuple Small\n  id Int\n'
chk("a big Dict key warns", TYPES + 'm Dict[Big, Int] = Dict()\n', True, None, "a Dict key of 80 bytes")
chk("a big Set element warns", TYPES + 's Set[Big] = Set()\n', True, None, "a Set element of 80 bytes")
chk("a small key does not", TYPES + 'm Dict[Small, Int] = Dict()\n', False)
chk("an integer key does not", 'm Dict[Int, String] = Dict()\n', False)
chk("a String key has no fixed size and does not warn", 'm Dict[String, Int] = Dict()\n', False)
chk("the threshold is settable", TYPES + 'm Dict[Big, Int] = Dict()\n', False, 'name = "k"\n[program]\nkey_warning = "128B"\n')
chk("a lower threshold warns for a small key", TYPES + 'm Dict[Small, Int] = Dict()\n', True, 'name = "k"\n[program]\nkey_warning = "4B"\n', "a Dict key of 8 bytes")
chk("zero turns the warning off", TYPES + 'm Dict[Big, Int] = Dict()\n', False, 'name = "k"\n[program]\nkey_warning = 0\n')
rc, out = check('println(1)\n', 'name = "k"\n[program]\nkey_warning = "big"\n')
ok = rc != 0 and "key_warning must be a size" in out
print(("ok    " if ok else "FAIL  ") + "a bad size is refused" + ("" if ok else f"  {out[:200]!r}"))
if not ok: fails.append("bad size")
print()
print("FAILURES: " + ", ".join(fails) if fails else "all key warning tests passed")
sys.exit(1 if fails else 0)
