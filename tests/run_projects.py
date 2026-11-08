"""Package and manifest rules: import cycles, clashes, rebinding, manifest typos.  Run: python3 tests/run_projects.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def proj(main, pkgs, manifest="", cmd="check"):
    d = tempfile.mkdtemp()
    if manifest: open(os.path.join(d, "Moxie.toml"), "w").write(manifest)
    for k, v in pkgs.items(): open(os.path.join(d, k + ".mxi"), "w").write(v)
    open(os.path.join(d, "main.mxi"), "w").write(main)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, os.path.join(d, "main.mxi")], cwd=d, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT), input="", timeout=60)
    return r.returncode, r.stdout + r.stderr
CYC = {"a": 'import b\nexport fn f() Int: b.g()\n', "b": 'import a\nexport fn g() Int: 1\n'}
CASES = [
 ("an import cycle is an error (check)", 'import a\nprintln(a.f())\n', CYC, "", "check", 1, "import cycle: a -> b -> a"),
 ("an import cycle is an error (run)", 'import a\nprintln(a.f())\n', CYC, "", "run", 2, "import cycle"),
 ("an import that clashes with a binding", 'f = 1\nimport a (f)\nprintln(f)\n', {"a": 'export fn f() Int: 1\n'}, "", "check", 1, "clashes with a name already in this file"),
 ("a library file may not bind a name twice", 'import a\nprintln(a.f())\n', {"a": 'x = 1\nx = 2\nexport fn f() Int: x\n'}, "", "check", 1, "may not rebind a module-level name"),
 ("the entry file may rebind", 'x = 1\nx = 2\nprintln(x)\n', {}, "", "run", 0, "2"),
 ("a clean import runs", 'import a\nprintln(a.f())\n', {"a": 'x = 1\nexport fn f() Int: x\n'}, "", "run", 0, "1"),
 ("a typo in a manifest key is suggested", 'println(1)\n', {}, '[program]\ntype_fuell = 5\n', "check", 2, "did you mean 'type_fuel'"),
 ("an unknown manifest table is an error", 'println(1)\n', {}, '[progrm]\nx = 1\n', "check", 2, "did you mean 'program'"),
 ("an unknown permission is an error", 'println(1)\n', {}, '[permissions]\nfsx = true\n', "check", 2, "unknown permission"),
]
fails = []
for name, main, pkgs, man, cmd, rc_want, word in CASES:
    rc, o = proj(main, pkgs, man, cmd)
    ok = rc == rc_want and word in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> rc={rc} {o.strip()[:200]}"))
    if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
