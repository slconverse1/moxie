"""`mutable` blocks: real assignment to the block's own names.  Run: python3 tests/run_mutable.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CASES = [
 ('running totals fill an array in place', 'fn running_totals(xs Array[Int][5]) Array[Int][5]\n  mutable\n    out = xs\n    total = 0\n    for i in 0..<5\n      total += xs(i)\n      out(i) = total\n    out\nprintln(running_totals(Array(3, 1, 4, 1, 5)))\n', 0, 'Array(3, 4, 8, 9, 14)'),
 ('assignment reaches through nested blocks', 'pure fn count_big(xs List[Int]) Int\n  mutable\n    n = 0\n    for x in xs\n      if x > 10\n        n += 1\n    n\nprintln(count_big(List(5, 20, 30, 1)))\n', 0, '2'),
 ('a pure fn may hold a mutable block', 'pure fn s(xs List[Int]) Int\n  mutable\n    t = 0\n    for x in xs\n      t += x\n    t\nprintln(s(List(1, 2, 3)))\n', 0, '6'),
 ('fields, a while loop, a when arm and an in line', 'tuple P deriving show\n  x Int\n  y Int\nfn g(xs List[Int]) (Int, Int)\n  total = 100\n  r = mutable\n    in total\n    p = P(0, 0)\n    i = 0\n    for i < len(xs)\n      p.x += xs(i)\n      when xs(i) % 2\n        0 -> p.y += 1\n        _ -> total -= 1\n      i += 1\n    (p.x + p.y, total)\n  (r.0, total)\nprintln(g(List(1, 2, 3, 4)))\n', 0, '(12, 100)'),
 ('the outer name is unchanged unless it is on the in line', 'fn f() Int\n  n = 5\n  r = mutable\n    in n\n    n += 1\n    n\n  n * 10 + r\nprintln(f())\n', 0, '56'),
 ('a mutable name keeps its type', 'fn f() Int\n  mutable\n    n = 0\n    n = "no"\n    n\nprintln(f())\n', 2, 'keeps its type'),
 ('mutable stays a legal name', 'mutable = 3\nprintln(mutable + 1)\nfn f(mutable Int) Int = mutable * 2\nprintln(f(4))\n', 0, '4\n8'),
 ('an outer name not on the in line is not changed by a loop', 'fn f() Int\n  n = 0\n  mutable\n    for i in 0..<3\n      n += 1\n    0\n  n\nprintln(f())\n', 2, 'n@1'),
 ('a copy is a copy: later writes do not show through', 'fn f() Int\n  mutable\n    a = Array(1, 2, 3)\n    b = a\n    a(0) = 9\n    b(0)\nprintln(f())\n', 0, '1'),
 ('reads of an outer name with @, calls, ref and a nested do block', 'fn sort_desc(xs List[Int]) List[Int]\n  xs |> sort() |> reverse() |> collect()\nfn bump(ref a Array[Int][3]) Unit\n  a(0) = a(0) + 100\nfn f() Int\n  v = 7\n  total = 1\n  mutable\n    in total\n    total += v@1\n    total += total@1\n    arr = Array(1, 2, 3)\n    bump(ref arr)\n    s = sort_desc(List(3, 1, 2))\n    t = do\n      u = 5\n      u += 1\n      u\n    arr(1) = t + s(0)\n    total + arr(0) + arr(1)\nprintln(f())\n', 0, '119'),
 ('assigning to a parameter that is not on the in line is an error', 'fn f(a Array[Int][2]) Int\n  mutable\n    for i in 0..<2\n      a(i) = 0\n    a(0)\nprintln(f(Array(1, 2)))\n', 2, 'in a'),
 ('a block hands back what it mutated as its last line', 'fn part(a Array[Int][4]) (Array[Int][4], Int)\n  mutable\n    in a\n    n = 0\n    for i in 0..<4\n      if a(i) > 2\n        a(i) = 0\n        n += 1\n    (a, n)\nb, k = part(Array(1, 3, 2, 5))\nprintln("${b} ${k}")\n', 0, 'Array(1, 0, 2, 0) 2'),
 ('writing an element of an outer array in a loop, without @1, is an error', 'fn f() Int\n  a = Array(1, 2, 3)\n  for i in 0..<3\n    a(i) = 9\n  a(0)\nprintln(f())\n', 2, 'never changes'),
 ('a@1 writes the outer array', 'fn f() Int\n  a = Array(1, 2, 3)\n  for i in 0..<3\n    a@1(i) = 9\n  a(0)\nprintln(f())\n', 0, '9'),
 ('a field of an outer tuple written in a loop is the same mistake', 'tuple P deriving show\n  x Int\nfn f() Int\n  p = P(1)\n  for i in 0..<3\n    p.x = 9\n  p.x\nprintln(f())\n', 2, 'never changes'),
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
