"""When the checker can neither prove nor refute a `where` condition: a note and a run-time check by default, an error with `--prove` or
`[contracts] prove = true`.  Run: python3 tests/run_unknown.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GET = "fn get(xs List[Int], i Int where i >= 0 and i < len(xs)) Int = xs(i)\n"
UNKNOWN = GET + "fn pick(n Int) Int = get(List(1, 2, 3), n * n)\nprintln(pick(1))\nprintln(pick(2))\n"
PROVED = GET + "fn pick(xs List[Int], i Int) Int\n  if i >= 0 and i < len(xs)\n    get(xs, i)\n  else\n    0\nprintln(pick(List(4, 5), 1))\n"
REFUTED = GET + "println(get(List(1, 2, 3), -1))\n"
CASES = [
 ("unknown compiles with a note", UNKNOWN, ["check"], None, 0, "checked when the program runs"),
 ("unknown is checked at run time", UNKNOWN, ["run"], None, 1, "precondition failed in get"),
 ("--prove makes unknown an error", UNKNOWN, ["--prove", "check"], None, 2, "can't prove"),
 ("[contracts] prove = true makes unknown an error", UNKNOWN, ["check"], "[contracts]\nprove = true\n", 2, "can't prove"),
 ("a proved call has no note", PROVED, ["check"], None, 0, "main.mxi: ok"),
 ("a refuted call is an error either way", REFUTED, ["check"], None, 2, "can never be true"),
]
fails = []
for name, src, args, toml, rc, want in CASES:
    for gc in (False, True):
        d = tempfile.mkdtemp()
        open(os.path.join(d, "main.mxi"), "w").write(src)
        open(os.path.join(d, "Moxie.toml"), "w").write('name = "t"\nentry = "main.mxi"\n' + (toml or ""))
        # a flag goes before the command, the file after it
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + args + [os.path.join(d, "main.mxi")]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        o = (r.stdout + r.stderr)
        ok = want in o and (r.returncode == 0) == (rc == 0)
        if name == "a proved call has no note":
            ok = ok and "warning" not in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o[:260]!r}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
