"""Refined element types: `List[Pos]`, `Array[Pos][N]`, `Set[Pos]`, `Dict[K, Pos]` in parameters, results, fields and bindings; checked when the program runs.
Run: python3 tests/run_refinedelems.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POS = 'type Pos = Int where self > 0\n'
CASES = [
 ('a parameter of refined elements accepts good ones', POS + 'fn total(xs List[Pos][3]) Int\n  reduce(0, (a, b) -> a + b, xs)\nprintln(total(List(1, 2, 3)))\n', 0, '6'),
 ('a parameter of refined elements aborts on a bad one', POS + 'fn total(xs List[Pos][3]) Int\n  reduce(0, (a, b) -> a + b, xs)\nprintln(total(List(1, 0, 3)))\n', 1, 'requires failed in total'),
 ('a binding checks every element', POS + 'ys List[Pos][2] = List(3, -4)\nprintln(len(ys))\n', 1, '`ys` must satisfy'),
 ('a binding of good elements is fine', POS + 'ys List[Pos][2] = List(3, 4)\nprintln(len(ys))\n', 0, '2'),
 ('a field checks every element at construction', POS + 'tuple Bag deriving show\n  items List[Pos][2]\nb = Bag(items: List(1, 0))\nprintln(len(b.items))\n', 1, 'invariant of Bag failed'),
 ('a field of good elements is fine', POS + 'tuple Bag deriving show\n  items List[Pos][2]\nb = Bag(items: List(1, 2))\nprintln(len(b.items))\n', 0, '2'),
 ('a result of refined elements is checked', POS + 'fn bad() List[Pos][2]\n  List(1, -1)\nprintln(len(bad()))\n', 1, 'ensures failed in bad'),
 ('Dict values are checked', POS + 'd Dict[String, Pos][2] = Dict("a" -> 1, "b" -> -2)\nprintln(len(d))\n', 1, '`d` must satisfy'),
 ('an Array of refined elements is checked', POS + 'a Array[Pos][2] = (5, 0)\nprintln(a(0))\n', 1, '`a` must satisfy'),
 ('a plain List is untouched', 'xs List[Int][2] = List(0, -1)\nprintln(len(xs))\n', 0, '2'),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        s = src if not gc else src.replace("][3]", "]").replace("][2]", "]")
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(s)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = ((r.returncode != 0) if rc_want else r.returncode == 0) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:220]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
