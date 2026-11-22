"""Spreading a Dict into a Dict literal.  Run: python3 tests/run_dictspread.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ('a spread copies the entries and a later entry replaces one in place', 'ages = Dict[String, Int][10]("alice" -> 30, "bob" -> 25, "carol" -> 41)\nolder = Dict(...ages, "alice" -> 31)\nfor (name, age) in older\n  println("$name is $age")\n', 0, 'alice is 31\nbob is 25\ncarol is 41'),
 ('the original is unchanged', 'ages = Dict("alice" -> 30, "bob" -> 25)\nolder = Dict(...ages, "alice" -> 31, "dave" -> 7)\nprintln("${len(ages)} ${len(older)}")\nprintln(ages("alice"))\n', 0, '2 3\nOk(30)'),
 ('new keys follow the spread, several spreads in order', 'a = Dict("x" -> 1, "y" -> 2)\nb = Dict("y" -> 20, "z" -> 30)\nc = Dict(...a, ...b, "w" -> 0)\nfor (k, v) in c\n  println("$k $v")\n', 0, 'x 1\ny 20\nz 30\nw 0'),
 ('capacity still applies', 'a = Dict("x" -> 1, "y" -> 2)\nb = Dict[String, Int][2](...a, "z" -> 3)\nprintln(len(b))\n', 1, 'capacity'),
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
