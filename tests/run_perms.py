"""Permission tests (Spec 19d).  Run: python3 tests/run_perms.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
os.makedirs(os.path.join(D, "data"))
os.makedirs(os.path.join(D, "other"))
open(os.path.join(D, "data", "a.txt"), "w").write("hello")
open(os.path.join(D, "other", "b.txt"), "w").write("secret")
fails = []


def run(src, *flags, manifest=None, cmd="run", extra=()):
    d = tempfile.mkdtemp(dir=D)
    for sub in ("data", "other"):
        os.makedirs(os.path.join(d, sub))
        open(os.path.join(d, sub, "a.txt" if sub == "data" else "b.txt"), "w").write("hello" if sub == "data" else "secret")
    if manifest is not None:
        open(os.path.join(d, "Moxie.toml"), "w").write(manifest)
    p = os.path.join(d, "main.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, p, *extra], cwd=d, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT), input="line one\n")
    return r.returncode, r.stdout + r.stderr


def chk(name, got, rc, word):
    code, out = got
    good = code == rc and word in out
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={code} {out.strip()[:240]}"))
    if not good:
        fails.append(name)


RD = 'println(read_file("data/a.txt"))\nprintln(read_file("other/b.txt"))\n'
chk("unrestricted by default", run(RD), 0, "Ok(\"secret\")")
chk("--allow-read=PATH allows inside and denies outside", run(RD, "--allow-read=data"), 0, "Ok(\"hello\")")
chk("outside the allowed path is DENIED", run(RD, "--allow-read=data"), 0, "code: 10")
chk("a path cannot climb out with ..", run('println(read_file("data/../other/b.txt"))\n', "--allow-read=data"), 0, "code: 10")
chk("write is separate from read", run('println(write_file("data/new.txt", "x"))\n', "--allow-read=data"), 0, "fs.write is not permitted")
chk("write denied where only read is granted (runtime)", run('println(write_file("data/new.txt", "x"))\nprintln(read_file("data/a.txt"))\n', "--allow-read=data", "--allow-write=other"), 0, "code: 10")
chk("write allowed in its path", run('println(write_file("other/n.txt", "x"))\n', "--allow-write=other"), 0, "Ok(())")
chk("open_file checks the mode", run('println(open_file("other/b.txt", Create))\n', "--allow-read=other"), 0, "code: 10")
chk("--allow-all lifts the limit", run(RD, "--deny-all", "--allow-all"), 0, "Ok(\"secret\")")
chk("--deny-all denies a file read statically", run(RD, "--deny-all"), 2, "needs fs.read or fs.write")
chk("the static error names the call and the source", run(RD, "--deny-all"), 2, "command line")
chk("stdout and stderr are always allowed", run('println("hi")\neprintln("err")\n', "--deny-all"), 0, "hi")
chk("stdin needs a grant (static)", run('println(read_line())\n', "--deny-all"), 2, "needs stdin")
chk("stdin granted", run('println(read_line())\n', "--allow-stdin"), 0, "line one")
chk("env without a grant is a compile error", run('println(len(env))\n', "--allow-read"), 2, "needs env")
chk("env is empty only when restricted, else filled", run('println(len(env) > 0)\n'), 0, "true")
chk("env granted", run('println(len(env) > 0)\n', "--allow-env"), 0, "true")
chk("connect checks host and port", run('println(connect("127.0.0.1", 1))\n', "--allow-connect=example.com:443"), 0, "code: 10")
chk("a connect pattern can use a wildcard", run('println(connect("127.0.0.1", 1))\n', "--allow-connect=127.0.0.1:*"), 0, "code: 11")
chk("listen is by port", run('println(listen(7))\n', "--allow-listen=8000-8010"), 0, "code: 10")
chk("net not granted at all is a compile error", run('println(connect("127.0.0.1", 1))\n', "--allow-read"), 2, "needs net")
chk("a foreign library needs ffi", run('foreign "m":\n  pure fn cos(x: Double) Double\nprintln(cos(0.0))\n', "--deny-all"), 2, "ffi for 'm'")
chk("a granted library loads", run('foreign "m":\n  pure fn cos(x: Double) Double\nprintln(cos(0.0))\n', "--allow-ffi=m"), 0, "1.0")
chk("a call through a function is still seen", run('fn grab(p: String) Result[String, Error]: read_file(p)\nprintln(grab("data/a.txt"))\n', "--deny-all"), 2, "needs fs")
chk("flags after the file go to the program", run('println(args)\n', extra=("--allow-all",)), 0, "--allow-all")
chk("Connection.open checks files", run('c = Connection.open("data/x.db")\nprintln(c)\n', "--allow-read=data"), 0, "code: 10")

M = '[permissions]\nfs.read = ["data"]\n'
chk("a manifest grants and restricts", run(RD, manifest=M), 0, "code: 10")
chk("a manifest grant allows its path", run(RD, manifest=M), 0, "Ok(\"hello\")")
chk("flags replace the manifest", run(RD, "--allow-read=other", manifest=M), 0, "Ok(\"secret\")")
chk("a manifest without [permissions] is unrestricted", run(RD, manifest='name = "x"\n'), 0, "Ok(\"secret\")")
chk("an empty [permissions] denies", run(RD, manifest="[permissions]\n"), 2, "needs fs")
chk("fs = true grants everything in fs", run(RD, manifest="[permissions]\nfs = true\n"), 0, "Ok(\"secret\")")
chk("an unknown permission is an error", run(RD, manifest="[permissions]\nfiles = true\n"), 2, "unknown permission")
chk("a bad value is an error", run(RD, manifest='[permissions]\nstdin = "yes"\n'), 2, "true or false")
chk("moxie check reports a missing grant", run(RD, "--deny-all", cmd="check"), 1, "needs fs")
# ---- per-package ceilings (Spec 19d)
def runp(main, pkgs, manifest, *flags, cmd="run"):
    d = tempfile.mkdtemp(dir=D)
    for sub, name, text in (("data", "a.txt", "hello"), ("other", "b.txt", "secret")):
        os.makedirs(os.path.join(d, sub))
        open(os.path.join(d, sub, name), "w").write(text)
    open(os.path.join(d, "Moxie.toml"), "w").write(manifest)
    for nm, text in pkgs.items():
        open(os.path.join(d, nm + ".mxi"), "w").write(text)
    p = os.path.join(d, "main.mxi")
    open(p, "w").write(main)
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, p], cwd=d, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT), input="")
    return r.returncode, r.stdout + r.stderr


READER = 'export fn slurp(p: String) Result[String, Error]: read_file(p)\nexport fn apply(f: (String) -> Result[String, Error], p: String) Result[String, Error]: f(p)\n'
MAIN = 'import reader\nprintln(read_file("data/a.txt"))\nprintln(reader.slurp("data/a.txt"))\nprintln(reader.slurp("other/b.txt"))\n'
ALL = '[permissions]\nall = true\n'
chk("a package with an empty table cannot read (static)", runp(MAIN, {"reader": READER}, ALL + '[permissions.packages.reader]\n'), 2, "package 'reader' (reader.mxi:1): 'read_file' needs fs.read or fs.write")
chk("the static error stands on the import line", runp(MAIN, {"reader": READER}, ALL + '[permissions.packages.reader]\n'), 2, "main.mxi:1: error: package 'reader'")
chk("a package with no table keeps the program's grants", runp(MAIN, {"reader": READER}, ALL), 0, "Ok(\"secret\")")
chk("a package ceiling limits paths at run time", runp(MAIN, {"reader": READER}, ALL + '[permissions.packages.reader]\nfs.read = ["data"]\n'), 0, "code: 10")
chk("the denial names the package", runp(MAIN, {"reader": READER}, ALL + '[permissions.packages.reader]\nfs.read = ["data"]\n'), 0, "for package reader")
chk("the ceiling still allows what it grants", runp(MAIN, {"reader": READER}, ALL + '[permissions.packages.reader]\nfs.read = ["data"]\n'), 0, "Ok(\"hello\")")
chk("the program itself is not limited by a package ceiling", runp(MAIN, {"reader": READER}, ALL + '[permissions.packages.reader]\nfs.read = ["data"]\n'), 0, "Ok(\"hello\")\nOk(\"hello\")")
chk("the program's grants limit the package too", runp(MAIN, {"reader": READER}, '[permissions]\nfs.read = ["data"]\n[permissions.packages.reader]\nfs.read = ["data", "other"]\n'), 0, "code: 10")
CB = 'import applier\nfn rd(p: String) Result[String, Error]: read_file(p)\nprintln(applier.apply(rd, "other/b.txt"))\n'
APPLIER = 'export fn apply(f: (String) -> Result[String, Error], p: String) Result[String, Error]: f(p)\n'
chk("a function written in the program keeps the program's rights", runp(CB, {"applier": APPLIER}, ALL + '[permissions.packages.applier]\n'), 0, "Ok(\"secret\")")
chk("a ceiling for a package nobody imports is a warning", runp('println(1)\n', {}, ALL + '[permissions.packages.ghost]\n', cmd="check"), 0, "warning: no imported package is named 'ghost'")
chk("a package table with an unknown kind is an error", runp(MAIN, {"reader": READER}, ALL + '[permissions.packages.reader]\nfiles = true\n'), 2, "unknown permission")
chk("flags replace the program's grants but not the ceilings", runp(MAIN, {"reader": READER}, ALL + '[permissions.packages.reader]\nfs.read = ["data"]\n', "--allow-all"), 0, "code: 10")
chk("a package that needs ffi is checked against its ceiling", runp('import m\nprintln(m.f())\n', {"m": 'foreign "m":\n  pure fn cos(x: Double) Double\nexport fn f() Double: cos(0.0)\n'}, ALL + '[permissions.packages.m]\n'), 2, "ffi for 'm'")

print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
