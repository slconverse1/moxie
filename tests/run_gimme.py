"""gimme in loops and blocks.  Run: python3 tests/run_gimme.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ("gimme updates names bound before a loop", 'total = 0\ncount = 0\nfor score in List(70, 85, 90)\n  gimme.1.total += score\n  gimme.1.count += 1\nprintln("$total $count")\n', 0, "245 3"),
 ("reduce carries the state with no outer write", 'total = List(70, 85, 90) |> to_stream() |> reduce(0, (acc, s) -> acc + s)\nprintln(total)\n', 0, "245"),
 ("a plain rebinding in a loop does not leave it", 'total = 0\nfor s in List(1, 2, 3)\n  total += s\nprintln(total)\n', 0, "0"),
 ("gimme in a nested if", 'n = 1\nif true\n  n = 2\n  gimme.1.n = 10\n  println("${n} ${gimme.1.n}")\nprintln("$n")\n', 0, "2 10\n10"),
 ("gimme with nothing to reach is an error", 'fn f() Int\n  gimme.1.x = 5\n  1\nprintln(f())\n', 2, "no enclosing block binds"),
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
