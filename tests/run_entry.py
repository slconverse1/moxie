"""Running with no file named: ./Moxie.toml's entry, else ./main.mxi.  Run: python3 tests/run_entry.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []

def run(d, *args):
    env = dict(os.environ, PYTHONPATH=ROOT)
    r = subprocess.run([sys.executable, "-m", "moxie", *args], cwd=d, env=env, capture_output=True, timeout=60)
    return r.returncode, r.stdout.decode() + r.stderr.decode()

def chk(name, d, args, rc_want, *wants):
    rc, out = run(d, *args)
    ok = rc == rc_want and all(w in out for w in wants)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
    if not ok: fails.append(name)

def folder(**files):
    d = tempfile.mkdtemp(prefix="mxentry")
    for k, v in files.items():
        open(os.path.join(d, k.replace("_", ".", 1) if k.startswith("Moxie") else k.replace("__", ".")), "w").write(v)
    return d

empty = folder()
chk("no file and nothing to find", empty, ["run"], 2, "no main.mxi")
m = folder(main__mxi='println("main ${args}")\n')
chk("run uses main.mxi", m, ["run"], 0, "main Array()")
chk("arguments that are not files go to the program", m, ["run", "verbose", "x"], 0, 'Array("verbose", "x")')
chk("check uses main.mxi", m, ["check"], 0, "main.mxi: ok")
chk("a named file still wins", folder(main__mxi='println("main")\n', other__mxi='println("other")\n'), ["run", "other.mxi"], 0, "other")
chk("a missing named file is an error", m, ["run", "nope.mxi"], 2, "cannot read nope.mxi")
e = folder(Moxie_toml='name = "app"\nentry = "app.mxi"\n', app__mxi='println("app")\n', main__mxi='println("main")\n')
chk("the manifest's entry beats main.mxi", e, ["run"], 0, "app")
b = folder(Moxie_toml='name = "app"\nentry = "gone.mxi"\n', main__mxi='println("main")\n')
chk("an entry that does not exist is an error", b, ["run"], 2, "gone.mxi")
nm = folder(Moxie_toml='name = "app"\n', main__mxi='println("main")\n')
chk("a manifest with no entry falls back to main.mxi", nm, ["run"], 0, "main")
chk("pools uses main.mxi", m, ["pools"], 0, "pool tally")
chk("doc uses main.mxi", m, ["doc", "-o", os.path.join(m, "out")], 0, "wrote")
chk("pools with nothing to find", empty, ["pools"], 2, "no main.mxi")
chk("a bare file name still runs", m, ["main.mxi"], 0, "main")

print()
print("FAILURES: " + ", ".join(fails) if fails else "all entry tests passed")
sys.exit(1 if fails else 0)
