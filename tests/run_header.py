"""The pool header at start-up and the memory budget (Spec 3a).  Run: python3 tests/run_header.py"""
import json, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
PROG = '''fiber[2] fn w(tx: ChanW[Int]):
  write(tx, 2)
rx, tx = Chan[Int][1]()
run w(tx)
println(read(rx)?)
'''
NOLIMIT = '''fn w(tx: ChanW[Int]):
  write(tx, 2)
rx, tx = Chan[Int][1]()
run w(tx)
println(read(rx)?)
'''


def moxie(d, *args):
    r = subprocess.run([sys.executable, "-m", "moxie", *args], cwd=d, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT), timeout=60)
    return r.returncode, r.stdout + r.stderr


def project(src, manifest=None):
    d = tempfile.mkdtemp()
    open(os.path.join(d, "main.mxi"), "w").write(src)
    if manifest is not None:
        open(os.path.join(d, "Moxie.toml"), "w").write(manifest)
    return d


def chk(name, got, rc, *words):
    code, out = got
    good = code == rc and all(w in out for w in words)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={code} {out.strip()[:300]}"))
    if not good:
        fails.append(name)


d = project(PROG)
moxie(d, "pools", "main.mxi", "--header", "h.json")
h = json.load(open(os.path.join(d, "h.json")))
chk("the header names the counts, the fibers, and the program", (0, json.dumps(h)), 0, '"Chan": 1', '"largest": 3', '"program"')
chk("a program runs under its own header", moxie(d, "--header=h.json", "run", "main.mxi"), 0, "2")
open(os.path.join(d, "main.mxi"), "w").write(PROG.replace("write(tx, 2)", "write( tx,2 )   // changed layout and a comment") + "\n\n")
chk("changed layout, spacing, and comments keep the header valid", moxie(d, "--header=h.json", "run", "main.mxi"), 0, "2")
open(os.path.join(d, "main.mxi"), "w").write(PROG + "println(1)\n")
chk("a header made for other source text is refused", moxie(d, "--header=h.json", "run", "main.mxi"), 2, "other source text")
open(os.path.join(d, "main.mxi"), "w").write(PROG)
h2 = json.loads(json.dumps(h)); h2["pools"]["Chan"] = 0
json.dump(h2, open(os.path.join(d, "h2.json"), "w"))
chk("a pool held to a lower count aborts when it is full", moxie(d, "--header=h2.json", "run", "main.mxi"), 1, "pool for Chan is full")
h3 = json.loads(json.dumps(h)); h3["fibers"]["largest"] = 1
json.dump(h3, open(os.path.join(d, "h3.json"), "w"))
chk("the fiber count is held to the header", moxie(d, "--header=h3.json", "run", "main.mxi"), 1, "fiber blocks are all in use")
open(os.path.join(d, "bad.json"), "w").write("{}")
chk("a file that is not a header is refused", moxie(d, "--header=bad.json", "run", "main.mxi"), 2, "not a pool header")
chk("a missing header file is refused", moxie(d, "--header=nope.json", "run", "main.mxi"), 2, "cannot read the pool header")
chk("without a header nothing is held to a count", moxie(d, "run", "main.mxi"), 0, "2")

M = '[fibers]\nmemory = "{m}"\nstack = "{s}"\n[program]\nmemory = "{t}"\n'
d = project(PROG, M.format(m="512B", s="512B", t="1KiB"))
chk("fibers that do not fit [program] memory stop the start", moxie(d, "run", "main.mxi"), 2, "needs 3072 bytes", "3 fibers of 512 memory + 512 stack", "is 1024")
d = project(PROG, M.format(m="512B", s="512B", t="4KiB"))
chk("fibers that fit start", moxie(d, "run", "main.mxi"), 0, "2")
d = project(NOLIMIT, M.format(m="512B", s="512B", t="1MiB"))
chk("a fiber function with no limit cannot be budgeted", moxie(d, "run", "main.mxi"), 2, "a fiber function has no limit")
d = project(PROG, '[fibers]\nmemory = "512B"\n[program]\nmemory = "1MiB"\n')
chk("the budget needs both memory and stack", moxie(d, "run", "main.mxi"), 2, "needs both memory and stack")
d = project(PROG, '[program]\nmemory = "lots"\n')
chk("a malformed size is a manifest error", moxie(d, "run", "main.mxi"), 2, "must be a size")
d = project(PROG, '[program]\nmemory = "1MB"\n[fibers]\nmemory = "1KiB"\nstack = "1KiB"\n')
chk("KB is 1000-based and KiB is 1024-based", moxie(d, "run", "main.mxi"), 0, "2")
d = project(PROG, '[pools]\nheader = "pools.json"\n')
moxie(d, "pools", "main.mxi", "--header", "pools.json")
chk("[pools] header names the file to read", moxie(d, "run", "main.mxi"), 0, "2")
open(os.path.join(d, "main.mxi"), "a").write("println(3)\n")
chk("and a stale one from the manifest is refused", moxie(d, "run", "main.mxi"), 2, "other source text")
d = project(PROG)
moxie(d, "pools", "main.mxi", "--header", "h.json")
chk("moxie/gc has no pool header", moxie(d, "--gc", "--header=h.json", "run", "main.mxi"), 2, "moxie/gc has neither")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
