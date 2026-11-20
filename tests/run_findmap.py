"""find_map (F#'s tryPick), filter_map (choose) and position, as pipe stages and as methods.  Run: python3 tests/run_findmap.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = 'inputs = List("apple", "42", "100", "banana")\nfn num(s String) Option[Int] = parse_number(s).ok()\n'
CASES = [
    ("pipe", HEAD + 'println(inputs |> find_map(num))\n', 0, "Ok(42)"),
    ("method", HEAD + 'println(inputs.find_map(num).get_or(0))\n', 0, "42"),
    ("missing", HEAD + 'println(List("a", "b").find_map(num).get_or(-1))\n', 0, "-1"),
    ("missing is an Err", HEAD + 'println(List("a").find_map(num) is Err(_))\n', 0, "true"),
    ("choose", HEAD + 'println(inputs |> filter_map(num) |> collect())\n', 0, "List(42, 100)"),
    ("stops early on an endless range", 'println(1.. |> find_map((n) -> if n * n > 50 then Some(n) else None))\n', 0, "Ok(8)"),
    ("dict gets key and value", 'd = Dict("a" -> 1, "b" -> 2)\nprintln(d.find_map((k, v) -> if v == 2 then Some(k) else None).get_or("?"))\n', 0, "b"),
    ("position method", 'println(List("a", "b", "c").position((s) -> s == "c"))\n', 0, "Ok(2)"),
    ("wrong function type", HEAD + 'println(inputs |> find_map((s) -> s))\n', 1, "Option"),
]
bad = 0
for name, src, rc_want, want in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    out = (r.stdout + r.stderr).decode()
    ok = (r.returncode == 0) == (rc_want == 0) and want in out
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else "  " + repr(out[-120:])))
    bad += not ok
print(f"{bad} failed")
sys.exit(1 if bad else 0)
