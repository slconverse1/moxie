"""union, merge, merge_with: no-GC moxie returns a Result with the left capacity, moxie/gc returns the plain collection.
Run: python3 tests/run_merge.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECL = 'a = Set[Int][8](1, 2)\nb = Set[Int][8](2, 3)\nd = Dict[String, Int][4]("a" -> 1, "b" -> 2)\ne = Dict[String, Int][4]("b" -> 9, "c" -> 3)\n'
CASES = [
 ("union", DECL + 'println(union(a, b))\n', "Ok(Set(1, 2, 3))", "Set(1, 2, 3)"),
 ("merge, the right value wins", DECL + 'println(merge(d, e))\n', 'Ok(Dict("a": 1, "b": 9, "c": 3))', 'Dict("a": 1, "b": 9, "c": 3)'),
 ("merge_with combines a shared key", DECL + 'println(merge_with((x, y) -> x + y, d, e))\n', 'Ok(Dict("a": 1, "b": 11, "c": 3))', 'Dict("a": 1, "b": 11, "c": 3)'),
 ("union overflow is NO_SLOT", 'a = Set[Int][3](1, 2)\nb = Set[Int][3](3, 4)\nprintln(union(a, b))\n', 'Err(Error(code: 5, message: "Set is full"))', "Set(1, 2, 3, 4)"),
 ("merge overflow is NO_SLOT", 'd = Dict[String, Int][2]("a" -> 1)\ne = Dict[String, Int][2]("b" -> 1, "c" -> 2)\nprintln(merge(d, e))\n', 'Err(Error(code: 5, message: "Dict is full"))', 'Dict("a": 1, "b": 1, "c": 2)'),
 ("the result keeps the left capacity", DECL + 'r = union(a, b)?\nprintln(len(r))\n', "3", None),
 ("operands are not changed", DECL + '_ = union(a, b)\nprintln(len(a))\n', "2", "2"),
]
BAD = [
 ("moxie: union gives a Result", 'a = Set[Int][4](1)\nb = Set[Int][4](2)\ns: Set[Int] = union(a, b)\n', "mismatched types", False),
 ("moxie/gc: union gives the Set", 'a: Set[Int] = Set(1)\nb: Set[Int] = Set(2)\ns: Set[Int] = union(a, b)\nn: Int = union(a, b)\n', "mismatched types", True),
]
fails = []


def run(cmd, src, gc=False):
    f = os.path.join(tempfile.mkdtemp(), "main.mxi")
    open(f, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + [cmd, f], cwd=ROOT, capture_output=True, timeout=60)
    return r.returncode, r.stdout.decode() + r.stderr.decode()


for name, src, want_moxie, want_gc in CASES:
    for gc, want in ((False, want_moxie), (True, want_gc)):
        if want is None:
            continue
        rc, o = run("run", src, gc)
        ok = rc == 0 and o.strip() == want
        print(("ok    " if ok else "FAIL  ") + name + (" [gc]" if gc else "") + ("" if ok else f"  {o[:300]!r}"))
        if not ok:
            fails.append(name + (" gc" if gc else ""))
for name, src, want, gc in BAD:
    rc, o = run("check", src, gc)
    ok = rc != 0 and want in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
