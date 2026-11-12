"""Signatures that differ between moxie and moxie/gc (put), and the ones they share (remove, clear).  Run: python3 tests/run_sigs_dialect.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = 'd: Dict[String, Int] = Dict("a" -> 1)\nxs: List[Int] = List(1, 2)\n'
CASES = [
 # (dialect flags, source, expected text in the output of `check`, or None for a clean run)
 ([], 'a: Int = put(d, "b", 2)\n', "expected `Int`, found `Result[Dict[String, Int]"),
 (["--gc"], 'a: Int = put(d, "b", 2)\n', "expected `Int`, found `Dict[String, Int]`"),
 ([], 'a: Dict[String, Int] = put(d, "b", 2)\n', "expected `Dict[String, Int]`, found `Result"),
 ([], 'a = put(d, 3, 2)\n', "`put` can't take"),
 (["--gc"], 'a = put(d, 3, 2)\n', "`put` can't take"),
 ([], 'a: Int = remove(d, "a")\n', "expected `Int`, found `Dict[String, Int]`"),
 (["--gc"], 'a: Int = clear(xs)\n', "expected `Int`, found `List[Int]`"),
 ([], 'r = put(d, "a", 5)?\nprintln(r)\n', None),
 (["--gc"], 'r = put(d, "b", 2)\nprintln(r)\n', None),
 ([], 'e = remove(d, "a")\nprintln(e)\n', None),
]
fails = []
for flags, body, want in CASES:
    d = tempfile.mkdtemp()
    f = os.path.join(d, "main.mxi")
    open(f, "w").write(PRE + body)
    r = subprocess.run([sys.executable, "-m", "moxie"] + flags + ["check" if want else "run", f], cwd=ROOT, capture_output=True, timeout=60)
    o = r.stdout.decode() + r.stderr.decode()
    ok = (want in o) if want else (r.returncode == 0 and "error" not in o)
    name = f"{' '.join(flags) or 'moxie'}: {body.strip().splitlines()[0]}"
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
