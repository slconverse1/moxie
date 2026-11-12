"""`else:` as the last arm of when, select, and seq (Spec: else arm).  Run: python3 tests/run_else.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=()):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", *flags, f.name], cwd=ROOT, capture_output=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, (r.stdout + r.stderr).decode()

CASES = [
 ("when with a value", 'fn k(n: Int) String\n  when n\n    0 -> "zero"\n    else "other"\nprintln(k(0))\nprintln(k(7))\n', 0, "zero\nother\n"),
 ("when with a guard before else", 'fn k(n: Int) String\n  when n\n    x if x > 5 -> "big"\n    else "small"\nprintln(k(9))\nprintln(k(1))\n', 0, "big\nsmall\n"),
 ("when without a value", 'x = 5\nr = when\n  x < 3 -> "a"\n  x < 10 -> "b"\n  else "c"\nprintln(r)\nx2 = 50\nr2 = when\n  x2 < 3 -> "a"\n  else "c"\nprintln(r2)\n', 0, "b\nc\n"),
 ("select else", 'rx, tx = Chan[Int][1]()\nselect\n  case v = read(rx) -> println("got")\n  else println("nothing")\n', 0, "nothing\n"),
 ("seq else runs only when nothing else did", 'fn is_big(n: Int) Bool\n  n > 100\nfn halve(n: Int) Int\n  n / 2\nfn neg(n: Int) Int\n  0 - n\na = 500\n  |> seq\n    is_big -> halve()\n    else neg()\nb = 50\n  |> seq\n    is_big -> halve()\n    else neg()\nprintln("$a $b")\n', 0, "250 -50\n"),
 ("else with a block body", 'fn k(n: Int) String\n  when n\n    0 -> "zero"\n    else\n      m = n + 1\n      "next ${m}"\nprintln(k(4))\n', 0, "next 5\n"),
 ("the old else -> form is gone", 'n = 1\nr = when n\n  1 -> 2\n  else -> 3\n', 2, "syntax error"),
 ("else must be last in a when", 'n = 1\nr = when n\n  else 1\n  2 -> 3\n', 2, "must be the last arm"),
 ("else must be last in a select", 'rx, tx = Chan[Int][1]()\nselect\n  else println("a")\n  case v = read(rx) -> println("b")\n', 2, "must be the last arm"),
 ("else must be last in a seq", 'xs = List(1)\nys = xs |> to_stream() |> seq\n  else collect()\n  else collect()\n', 2, "must be the last arm"),
]
fails = []
for name, src, rc_want, want in CASES:
    for flags in ((), ("--gc",)):
        rc, out = run(src, flags)
        ok = rc == rc_want and want in out
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if flags else "") + ("" if ok else f"  rc={rc} {out[:200]!r}"))
        if not ok: fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
