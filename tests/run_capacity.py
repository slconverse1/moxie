"""A size written on a declaration must be the literal's: `a: Set[Int][8] = Set(1, 2)` is an error in no-GC moxie, and room is
written on the constructor.  In moxie/gc a size is only a hint, so no error.  Run: python3 tests/run_capacity.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAD = [
 ("Set larger than its literal", 'a: Set[Int][8] = Set(1, 2)\n', "the declared size 8 does not match the 2 elements of this Set literal"),
 ("Set smaller than its literal", 'a: Set[Int][1] = Set(1, 2)\n', "the declared size 1 does not match the 2 elements"),
 ("List", 'b: List[Int][5] = List(1, 2, 3)\n', "the declared size 5 does not match the 3 elements of this List literal"),
 ("Dict", 'd: Dict[String, Int][8] = Dict("a" -> 1)\n', "does not match the 1 element of this Dict literal"),
 ("Array tuple", 'x: Array[Int][5] = (1, 2, 3)\n', "an Array has exactly the elements it is written with"),
 ("the message shows the constructor", 'a: Set[Int][8] = Set(1, 2)\n', "`Set[Int][8](...)`"),
]
OK = [
 ("sizes agree", 'a: Set[Int][2] = Set(1, 2)\nprintln(len(a))\n', "2"),
 ("no size", 'a = Set(1, 2)\nh: Array[Int] = (1, 2, 3)\nprintln("${len(a)} ${len(h)}")\n', "2 3"),
 ("room on the constructor", 'a = Set[Int][8](1, 2)\nb: Set[Int][8] = Set[Int][8](1, 2)\nprintln("${len(a)} ${len(b)}")\n', "2 2"),
 ("a duplicate constant counts once", 'a: Set[Int][1] = Set(1, 1)\nprintln(len(a))\n', "1"),
 ("an empty literal takes the declared size", 'a: List[Int][8] = List()\nprintln(len(a))\n', "0"),
 ("a comprehension takes the declared size", 'words = List("aa", "b")\nz: Dict[String, Int][8] = Dict(w -> len(w) for w in words)\nprintln(len(z))\n', "2"),
]
GC_OK = [("moxie/gc: a size is a hint", 'a: Set[Int][8] = Set(1, 2)\nprintln(len(a))\n', "2")]
fails = []


def run(cmd, src, gc=False):
    f = os.path.join(tempfile.mkdtemp(), "main.mxi")
    open(f, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + [cmd, f], cwd=ROOT, capture_output=True, timeout=60)
    return r.returncode, r.stdout.decode() + r.stderr.decode()


for name, src, want in BAD:
    rc, o = run("check", src)
    ok = rc != 0 and want in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name)
for name, src, want in OK + GC_OK:
    gc = (name, src, want) in GC_OK
    rc, o = run("run", src, gc)
    ok = rc == 0 and o.strip() == want
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name)
for name, src, want in OK:
    rc, o = run("run", src, True)
    ok = rc == 0 and o.strip() == want
    print(("ok    " if ok else "FAIL  ") + name + " [gc]" + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name + " gc")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
