"""is not, the bare `...` rest, for: skipping non-matching List items, filter_map.  Run: python3 tests/run_patterns2.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=(), cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, f.name], cwd=ROOT, capture_output=True, timeout=60)
        rc, out = r.returncode, r.stdout.decode() + r.stderr.decode()
    except subprocess.TimeoutExpired:
        rc, out = -9, "TIMEOUT"
    os.unlink(f.name)
    return rc, out

fails = []
def chk(name, src, rc_want, *wants, cmd="run"):
    for flags in ((), ("--gc",)):
        rc, out = run(src, flags, cmd)
        ok = rc == rc_want and all(w in out for w in wants)
        label = name + (" (gc)" if flags else "")
        print(("ok    " if ok else "FAIL  ") + label + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
        if not ok: fails.append(label)

U = "tuple User\n  name String,\n  age Int,\n  role String\nu = User(\"a\", 3, \"admin\")\n"
chk("is not", "o = Some(1)\nprintln(o is not Some(_))\nprintln(o is not None)\nx Int | String = 5\nprintln(x is not String)\n", 0, "false\ntrue\ntrue")
chk("is not in an if", U + "if u is not User(role: \"guest\", ...)\n  println(\"not guest\")\n", 0, "not guest")
chk("a bare ... in a tuple pattern", U + "println(u is User(name, ...))\nprintln(u is User(role: \"guest\", ...))\nUser(n, ...) = u\nprintln(n)\n", 0, "true\nfalse\na")
chk("a bare ... in a List pattern", "xs = List(1, 2, 3)\nprintln(xs is List(first, ...))\nwhen xs\n  List(a, ..., z) -> println(\"${a} ${z}\")\n  _ -> println(\"no\")\nprintln(List(1) is List(a, ..., z))\n", 0, "true\n1 3\nfalse")
chk("for: over a List skips items the pattern does not fit", "os = List(Some(1), None, Some(3))\nr = for\n  Some(x) in os\n  yield x * 2\nprintln(r)\n", 0, "List(2, 6)")
chk("for: pattern skip together with an if line", "ps = List(Some((1, \"a\")), None, Some((5, \"b\")))\nq = for\n  Some((n, w)) in ps\n  if n > 1\n  yield \"${n}${w}\"\nprintln(q)\n", 0, 'List("5b")')
chk("a plain for loop stays strict", "os = List(Some(1), None)\nfor Some(x) in os\n  println(x)\n", 2, "does not fit every element")
chk("filter_map keeps the Somes", "xs = List(1, 2, 3)\nprintln(xs |> filter_map((x) -> if x > 1 then Some(x * 10) else None) |> collect())\nprintln(xs.filter_map((x) -> if x == 2 then Some(\"two\") else None) |> collect())\n", 0, "List(20, 30)\nList(\"two\")")
chk("if ... is ... then ... else binds in the then branch", "o = Some(3)\nprintln(if o is Some(v) then v * 2 else 0)\nprintln(if o is Some(v) and v > 5 then v else -1)\n", 0, "6\n-1")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
