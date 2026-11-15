"""The declaration line (`total, count` first in a block).  Run: python3 tests/run_declline.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ('a loop starts its locals from the outer ones', 'total = 0\ncount = 0\nfor x in List(1, 2, 3)\n  in total, count\n  total += x\n  count += 1\nprintln("$total $count")\n', 0, '0 0'),
 ('the local leaves through break', 'total = 0\nr = for x in List(1, 2, 3)\n  in total\n  total += x\n  if x == 3 then break(total)\nelse\n  -1\nprintln(r)\n', 0, '6'),
 ('the local leaves through else', 'n = 0\nr = while n < 3\n  in n\n  n += 1\nelse n\nprintln(r)\n', 0, '3'),
 ('a plain block gets a copy', 'n = 5\nif true\n  in n\n  n += 10\n  println("${n} ${n@1}")\nprintln(n)\n', 0, '15 5\n5'),
 ('a function starts from a module-level name', 'total = 5\nfn f() Int\n  in total\n  total += 1\n  total\nprintln("${f()} $total")\n', 0, '6 5'),
 ('name@N picks the layer', 'n = 1\nif true\n  n = 2\n  if true\n    in n@2\n    n += 100\n    println("${n} ${n@1} ${n@2}")\n', 0, '101 2 1'),
 ('name@label picks the loop', 'total = 100\n#outer for i in List(1, 2)\n  total = 5\n  for j in List(1, 2)\n    in total@outer\n    total += j\n    println("${total} ${total@1}")\n', 0, '101 5\n103 5\n101 5\n103 5'),
 ('the outer one is still reachable with @1', 'n = 1\nif true\n  in n\n  n += 1\n  n@1 += 10\nprintln(n)\n', 0, '11'),
 ('nothing outside is an error', 'if true\n  in zz\n  zz += 1\n  println(zz)\n', 2, 'no outer `zz` to start from'),
 ('a name listed twice is an error', 'n = 1\nif true\n  in n, n\n  n += 1\n', 2, 'listed twice'),
 ('an unknown label is an error', 'n = 1\nfor x in List(1)\n  in n@nope\n  n += x\n', 2, 'no enclosing loop or `do` is labeled `#nope`'),
 ('without the line the self-shadow error stays', 'n = 0\nfor x in List(1)\n  n += x\nprintln(n)\n', 2, 'reads the outer `n`'),
 ('a lone name stays a value', 'fn f(a Int) Int\n  a\nprintln(f(4))\n', 0, '4'),
 ('a bare list of names first is not a declaration', 'n = 1\nif true\n  n, 2\n  println(n)\n', 0, '1'),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = (r.returncode == rc_want or (rc_want == 2 and r.returncode != 0)) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:200]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
