"""The pool header at start-up and the memory budget (Spec 3a).  Run: python3 tests/run_header.py"""
import json, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
PROG = '''fiber[2] fn w(tx: ChanW[Int]) Unit
  \\write(tx, 2)
rx, tx = Chan[Int][1]()
run w(tx)
println(read(rx)?)
'''
NOLIMIT = '''fiber fn w(tx: ChanW[Int]) Unit
  \\write(tx, 2)
rx, tx = Chan[Int][1]()
run w(tx)
println(read(rx)?)
'''


def moxie(d, *args):
    r = subprocess.run([sys.executable, "-m", "moxie", *args], cwd=d, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT), timeout=60)
    return r.returncode, r.stdout + r.stderr


def project(src, manifest=None, files=None):
    d = tempfile.mkdtemp()
    open(os.path.join(d, "main.mxi"), "w").write(src)
    for nm, text in (files or {}).items():
        open(os.path.join(d, nm), "w").write(text)
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
chk("fibers that do not fit [program] memory stop the start", moxie(d, "run", "main.mxi"), 2, "needs 3144 bytes", "72 for pools + 3 fibers of 512 memory + 512 stack", "is 1024")
d = project(PROG, M.format(m="512B", s="512B", t="4KiB"))
chk("fibers that fit start", moxie(d, "run", "main.mxi"), 0, "2")
S = '[fibers]\nstrings = "{a}"\ntemps = "{b}"\nstack = "{s}"\n[program]\nmemory = "{t}"\n'
d = project(PROG, S.format(a="256B", b="256B", s="512B", t="1KiB"))
chk("strings and temps add up to a fiber's memory", moxie(d, "run", "main.mxi"), 2, "3 fibers of 512 memory (256 strings + 256 temps) + 512 stack")
d = project(PROG, S.format(a="256B", b="256B", s="512B", t="4KiB"))
chk("strings and temps instead of memory start when they fit", moxie(d, "run", "main.mxi"), 0, "2")
d = project(PROG, '[fibers]\nmemory = "512B"\nstrings = "128B"\nstack = "512B"\n[program]\nmemory = "1KiB"\n')
chk("one of strings and temps with memory leaves the rest to the other", moxie(d, "run", "main.mxi"), 2, "(128 strings + 384 temps)")
d = project(PROG, '[fibers]\nmemory = "512B"\nstrings = "300B"\ntemps = "300B"\nstack = "512B"\n')
chk("strings plus temps must equal memory", moxie(d, "run", "main.mxi"), 2, "strings (300) plus temps (300) is 600, but memory says 512")
d = project(PROG, '[fibers]\nstrings = "300B"\nstack = "512B"\n')
chk("strings without temps or memory is an error", moxie(d, "run", "main.mxi"), 2, "needs both strings and temps")
d = project(PROG, '[fibers]\nmemory = "100B"\ntemps = "300B"\nstack = "512B"\n')
chk("a part larger than memory is an error", moxie(d, "run", "main.mxi"), 2, "larger than memory")
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
# ---- packages
LIB = '''export fn mk() ChanW[Int]
  rx, tx = Chan[Int][1]()
  tx
fiber[2] fn work(tx: ChanW[Int]) Unit
  \\write(tx, 7)
export fn go(tx: ChanW[Int]) Unit
  run work(tx)
'''
MAIN = '''import lib
rx, tx = Chan[Int][4]()
a = lib.mk()
b = lib.mk()
lib.go(tx)
println(read(rx)?)
'''
d = project(MAIN, files={"lib.mxi": LIB})
out = moxie(d, "pools", "main.mxi", "--header", "h.json")
chk("the tally follows calls into an imported package", out, 0, "Chan     3", "lib.work (limit 2)", "largest possible fiber count: 3")
chk("a program that uses a package runs under its header", moxie(d, "--header=h.json", "run", "main.mxi"), 0, "7")
open(os.path.join(d, "lib.mxi"), "w").write(LIB.replace("write(tx, 7)", "write( tx,7 )  // reformatted\n"))
chk("reformatting a package keeps the header valid", moxie(d, "--header=h.json", "run", "main.mxi"), 0, "7")
open(os.path.join(d, "lib.mxi"), "w").write(LIB.replace("Chan[Int][1]", "Chan[Int][2]"))
chk("changing a package makes the header stale", moxie(d, "--header=h.json", "run", "main.mxi"), 2, "other source text")
d = project("import lib (mk)\ntx = mk()\nprintln(1)\n", files={"lib.mxi": LIB})
chk("a function imported by name is followed", moxie(d, "pools", "main.mxi"), 0, "Chan     1")
d = project("import lib\nprintln(1)\n", files={"lib.mxi": 'rx, tx = Chan[Int][1]()\nexport fn f() Int = 1\n'})
chk("a package's top level is counted once it is imported", moxie(d, "pools", "main.mxi"), 0, "Chan     1")
d = project('import lib\nfor i in 0..3\n  t = lib.mk()\nprintln(1)\n', files={"lib.mxi": LIB})
chk("a kept resource from a package in a loop is an error naming the package", moxie(d, "pools", "main.mxi"), 1, "lib.mk' creates a Chan that outlives the call")
d = project('fiber[3] fn w(tx: ChanW[Int]) Unit\n  \\write(tx, 2)\nfn start(tx: ChanW[Int]) Unit\n  run w(tx)\nrx, tx = Chan[Int][4]()\nstart(tx)\nprintln(read(rx)?)\n')
chk("fibers started by a helper function are counted", moxie(d, "pools", "main.mxi"), 0, "largest possible fiber count: 4")
BOXLIB = '''export tuple Box
  n: Int
impl Box
  fn chan(self) ChanW[Int]
    rx, tx = Chan[Int][1]()
    tx
export fn new_box() Box = Box(1)
'''
d = project("import lib\nb = lib.new_box()\nt1 = b.chan()\nprintln(1)\n", files={"lib.mxi": BOXLIB})
chk("a package method called as x.method() is followed (UFCS)", moxie(d, "pools", "main.mxi"), 0, "Chan     1")
d = project("import lib\nb = lib.new_box()\nprintln(1)\n", files={"lib.mxi": BOXLIB})
chk("a package method that is not called is not counted", moxie(d, "pools", "main.mxi"), 0, "no counted resource")

# the pools themselves count in the budget (layout.py: slot sizes)
PB = '''rx, tx = Chan[Int][4]()
a = Atom[Int](0)
t = Timer(1s)
println("done")
'''
FM = '[fibers]\nlimit = 1\nmemory = "1KiB"\nstack = "1KiB"\n[program]\nmemory = "{t}"\n'
d = project(PB, FM.format(t="2200"))
chk("pools and fibers that exactly fit start", moxie(d, "run", "main.mxi"), 0, "done")
d = project(PB, FM.format(t="2199"))
chk("one byte less is refused, with the pools named", moxie(d, "run", "main.mxi"), 2, "needs 2200 bytes", "152 for pools")
chk("the pool report gives the pool memory", moxie(d, "pools", "main.mxi"), 0, "pool memory: 152 bytes")
TUP = '''tuple Point
  x: Double
  y: Float
rx, tx = Chan[Point][3]()
println(1)
'''
d = project(TUP, FM.format(t="4KiB"))
chk("a channel of a tuple type is sized from its fields", moxie(d, "pools", "main.mxi"), 0, "pool memory: 112 bytes")
d = project("rx, tx = Chan[String]()\nprintln(1)\n", FM.format(t="4KiB"))
chk("a pool whose size is not known cannot be budgeted", moxie(d, "run", "main.mxi"), 2, "the size of the pools is not known", "line 1", "Chan")
d = project("a = Atom(7)\nb = Atom(\"x\")\nprintln(1)\n", FM.format(t="4KiB"))
chk("an Atom with no type argument is sized from a literal, else it is not known", moxie(d, "run", "main.mxi"), 2, "write the type of the Atom")
FP = '''fiber[2] fn w(tx: ChanW[Int]) Unit
  rx2, tx2 = Chan[Int][1]()
  \\write(tx, 2)
rx, tx = Chan[Int][1]()
run w(tx)
println(read(rx)?)
'''
d = project(FP, FM.format(t="4KiB").replace("limit = 1", "limit = 3"))
chk("pools in a fiber function count once per possible fiber", moxie(d, "pools", "main.mxi"), 0, "pool memory: 216 bytes")
d = project(PB, FM.format(t="100"))
moxie(d, "pools", "main.mxi", "--header", "old.json")
oldh = json.load(open(os.path.join(d, "old.json"))); del oldh["bytes"]
json.dump(oldh, open(os.path.join(d, "old.json"), "w"))
chk("a header without sizes is not refused for them", moxie(d, "--header=old.json", "run", "main.mxi"), 2, "needs 2048 bytes")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
