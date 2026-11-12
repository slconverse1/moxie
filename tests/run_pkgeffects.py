"""Effects and permission needs across imported packages.  Run: python3 tests/run_pkgeffects.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []


def run(main, files, *flags, manifest=None, cmd="run"):
    d = tempfile.mkdtemp()
    open(os.path.join(d, "main.mxi"), "w").write(main)
    for nm, text in files.items():
        open(os.path.join(d, nm), "w").write(text)
    if manifest:
        open(os.path.join(d, "Moxie.toml"), "w").write(manifest)
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, os.path.join(d, "main.mxi")], cwd=d, capture_output=True,
                       text=True, env=dict(os.environ, PYTHONPATH=ROOT), timeout=60)
    return r.returncode, r.stdout + r.stderr


def chk(name, got, rc, *words):
    code, out = got
    good = code == rc and all(w in out for w in words)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={code} {out.strip()[:300]}"))
    if not good:
        fails.append(name)


LIB = '''export fn shout() Int
  println("hi")
  1
export pure fn twice(n: Int) Int = n * 2
export fn slurp(p: String) Result[String, Error] = read_file(p)
export fn apply(f: () -> Int) Int = f()
export tuple Box
  n: Int
impl Box
  export fn say(self) Int
    println("box")
    self.n
export fn new_box() Box = Box(1)
'''
F = {"lib.mxi": LIB}
chk("a pure function that calls a printing package function is an error", run('import lib\npure fn f() Int = lib.shout()\nprintln(f())\n', F), 2, "prints (calls 'println')")
chk("so is one that imports the function by name", run('import lib (shout)\npure fn f() Int = shout()\nprintln(f())\n', F), 2, "prints")
chk("a pure package function keeps a pure caller pure", run('import lib\npure fn f() Int = lib.twice(2)\nprintln(f())\n', F), 0, "4")
chk("a package method called as x.method() carries its effect", run('import lib\npure fn f(b: lib.Box) Int = b.say()\nprintln(f(lib.new_box()))\n', F), 2, "prints")
chk("a function passed to a package function that calls it carries its effect", run('import lib\npure fn f() Int = lib.apply(shout)\nfn shout() Int\n  println("x")\n  1\nprintln(f())\n', F), 2, "prints")
chk("a pure function passed to a package function is fine", run('import lib\npure fn f() Int = lib.apply(() -> 5)\nprintln(f())\n', F), 0, "5")
chk("a restricted program that reaches a package's file read is a compile error", run('import lib\nprintln(lib.slurp("x"))\n', F, "--deny-all"), 2, "needs fs.read or fs.write")
chk("a package function that is never called adds no need", run('import lib\nprintln(lib.twice(2))\n', F, "--deny-all"), 0, "4")
chk("a package's top level counts when it is imported", run('import tp\nprintln(1)\n', {"tp.mxi": 'x = read_file("f")\nexport fn k() Int = 1\n'}, "--deny-all"), 2, "needs fs")
chk("a granted program runs the package call", run('import lib\nprintln(lib.slurp("nope"))\n', F, "--allow-read"), 0, "code: 9")
chk("a package that calls another package needs no ceiling for the callee's work", run('import mid\nprintln(mid.f())\n', {"lib.mxi": LIB, "mid.mxi": 'import lib\nexport fn f() Int = lib.twice(3)\n'}, manifest='[permissions]\nall = true\n[permissions.packages.mid]\n'), 0, "6")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
