"""Several Dict entries at once, `{a, b} -> (1, 2)`, and tuple keys in a Dict literal.  Run: python3 tests/run_dictmulti.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ('several entries at once', 'ages = Dict(alice -> 30, bob -> 25, carol -> 41)\nolder = Dict(...ages, {alice, bob, dave} -> (31, 26, 7))\nfor (name, age) in older\n  println("$name is $age")\n', 0, 'alice is 31\nbob is 26\ncarol is 41\ndave is 7'),
 ('mixed with ordinary entries and quoted keys', 'm = Dict({"x", "y"} -> (1, 2), z -> 3)\nprintln(m)\n', 0, 'Dict("x" -> 1, "y" -> 2, "z" -> 3)'),
 ('values are any expressions', 'n = 10\nm = Dict({a, b} -> (n + 1, n * 2))\nprintln(m)\n', 0, 'Dict("a" -> 11, "b" -> 20)'),
 ('one key takes one value', 'm = Dict({a} -> 5)\nprintln(m)\n', 0, 'Dict("a" -> 5)'),
 ('a tuple key is one entry', 'cells = Dict((0, 0) -> "start", (1, 2) -> "goal")\nprintln("${len(cells)} ${cells((1, 2))}")\n', 0, 'Ok("goal")'),
 ('a tuple key with a tuple value is one entry', 'm = Dict((1, 2) -> (3, 4))\nprintln(m((1, 2)))\n', 0, 'Ok((3, 4))'),
 ('a lambda argument elsewhere is still a lambda', 'xs = List(1, 2, 3)\nprintln(map((x) -> x * 2, xs) |> collect())\n', 0, 'List(2, 4, 6)'),
 ('too few values is an error', 'm = Dict({a, b, c} -> (1, 2))\n', 2, '3 keys need a tuple of 3 values'),
 ('a lone value for several keys is an error', 'm = Dict({a, b} -> 1)\n', 2, '2 keys need a tuple of 2 values'),
 ('braces outside a Dict are an error', 'x = List({a} -> (1))\n', 2, 'does not start an expression'),
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
