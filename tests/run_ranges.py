"""Stepped ranges: `a..b step s`, `in`, slices, len, indices, clamp, random_int(range).  Run: python3 tests/run_ranges.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CASES = [
 ('step counts up', 'for i in 1..=9 step 4\n  print("${i} ")\nprintln("")\n', 0, '1 5 9'),
 ('a negative step counts down', 'for i in 10..1 step -3\n  print("${i} ")\nprintln("")\n', 0, '10 7 4'),
 ('a negative step counts down with variable bounds', 'lo = 12\nhi = 3\nfor i in lo..hi step -4\n  print("${i} ")\nprintln("")\n', 0, '12 8 4'),
 ('a wrong-way step with variable bounds is empty', 'n = 10\nfor i in n..1 step 3\n  print("x")\nprintln("empty")\n', 0, 'empty'),
 ('a wrong-way literal step is a compile error', 'for i in 10..1 step 3\n  println(i)\n', 2, 'write `step -3`'),
 ('a wrong-way negative literal step is a compile error', 'for i in 1..9 step -2\n  println(i)\n', 2, 'write `step 2`'),
 ('a zero step is an error', 'for i in 1..9 step 0\n  println(i)\n', 2, "can't be 0"),
 ('in honours the step', 'println("${3 in 1..=9 step 2} ${4 in 1..=9 step 2} ${7 in 10..1 step -3} ${5 in 10..1 step -3}")\n', 0, 'true false true false'),
 ('in with an unstepped descending literal range', 'println("${5 in 10..1} ${10 in 10..1} ${1 in 10..1}")\n', 0, 'true true false'),
 ('a stepped slice picks every nth element', 'xs = List("a", "b", "c", "d", "e")\nprintln(xs(0..=4 step 2))\nprintln(xs(4..0 step -2))\nprintln("Kotlin"(0..6 step 2))\n', 0, 'List("a", "c", "e")\nList("e", "c")\nKti'),
 ('a stepped slice past the end aborts', 'xs = List(1, 2, 3)\nprintln(xs(0..=9 step 2))\n', 1, 'out of range'),
 ('a range value shows its step and answers len and step', 'r = 1..=9 step 4\nprintln("${r} ${len(r)} ${step(r)} ${start(r)} ${limit(r)}")\n', 0, '1..=9 step 4 3 4 1 9'),
 ('a stepped range in a pipeline', 'println(1..=7 step 3 |> map(_ * 10) |> collect())\n', 0, 'List(10, 40, 70)'),
 ('a stepped range in a comprehension', 'println(List(x * x for x in 1..=9 step 4))\n', 0, 'List(1, 25, 81)'),
 ('a stepped range in a when arm', 'x = 5\nr = when x\n  1..=9 step 2 -> "odd"\n  else "other"\nprintln(r)\n', 0, 'odd'),
 ('step is a legal name elsewhere', 'step = 3\nprintln(step + 1)\nfn f(step Int) Int = step * 2\nprintln(f(4))\nfor i in 0..step\n  print("${i}")\nprintln("")\n', 0, '4\n8\n012'),
 ('an open-ended stepped range', 'println(1.. step 5 |> take_while(_ < 20) |> collect())\n', 0, 'List(1, 6, 11, 16)'),
 ('Range(a..b, s) is gone', 'for i in Range(1..9, 2)\n  println(i)\n', 2, '`Range(a..b, s)` is gone'),
 ('indices is 0..len', 'xs = List(10, 20, 30)\nprintln("${4 in indices(xs)} ${2 in indices(xs)} ${len(indices(xs))}")\n', 0, 'false true 3'),
 ('clamp takes a closed range', 'println(clamp(120, 0..=100))\nprintln(clamp(-5, 0..=100))\nprintln(clamp(50, 0..=100))\n', 0, '100\n0\n50'),
 ('random_int takes a range', 'println(random_int(5..=5))\nok = true\nfor i in 0..100\n  r = random_int(1..=9 step 2)\n  if r % 2 == 0 or r > 9\n    ok = false\nprintln(ok)\n', 0, '5\ntrue'),
 ('random_int(lo, hi) is gone', 'println(random_int(1, 6))\n', 2, '`random_int` takes a range'),
 ('random_int on an empty range aborts', 'a = 5\nb = 1\nprintln(random_int(a..=b))\n', 1, 'is empty'),
 ('first and last give the values a stepped range reaches', 'r = 1..10 step 4\nprintln("${first(r)} ${last(r)} ${last(10..1 step -3)}")\n', 0, 'Ok(1) Ok(9) Ok(4)'),
 ('a field a Range does not have is a clear error', 'r = 1..=9 step 4\nprintln(r.last)\n', 1, 'use first(r) and last(r)'),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in ((True,) if src.startswith('#gc') else (False, True)):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = ((r.returncode != 0) if rc_want else r.returncode == 0) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
