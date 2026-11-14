"""One code for "that element is not there": MISSING (4) for a Dict key, a List index, `first` of nothing and an enum case; OUT_OF_RANGE (6) stays for numbers.  Run: python3 tests/run_notfound.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
ENUM = 'enum Color\n  Red\n  Green\n'
CASES = [
 ("a Dict key", 'd = Dict(("a", 1))\nprintln(get(d, "z"))\nprintln(d("z"))\n', 'code: 4, message: "no such key"'),
 ("a List index", 'xs = List(1, 2)\nprintln(get(xs, len(xs) + 3))\n', 'code: 4, message: "no such element"'),
 ("an Array index", 'a = Array(1, 2)\nprintln(get(a, len(a) + 3))\n', 'code: 4, message: "no such element"'),
 ("first of an empty List", 'println(first(List[Int]()))\n', 'code: 4, message: "empty"'),
 ("an enum case by name", ENUM + 'println(Color.value_of("Blue"))\n', "code: 4"),
 ("an enum case by position", ENUM + 'println(Color.from_index(5))\n', "code: 4, message: \"no such case\""),
 ("a number out of range stays OUT_OF_RANGE", 'println(try_cast[UInt8](300))\n', "code: 6"),
 ("get_or still gives the default", 'xs = List(1)\nprintln(get_or(xs, len(xs) + 3, 9))\n', "9"),
 ("the codes are the named ones", 'xs = List(1)\nprintln(get(xs, len(xs) + 3) == fail(MISSING, "no such element"))\n', "true"),
]
fails = []
for name, src, word in CASES:
    p = os.path.join(D, "t.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", p], cwd=ROOT, capture_output=True, text=True)
    o = r.stdout + r.stderr
    good = r.returncode == 0 and word in o
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={r.returncode} {o.strip()[:300]!r}"))
    if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
