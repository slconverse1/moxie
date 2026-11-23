"""par_map, par_traverse, and par_map_all need a constant `limit:`, written directly or after a pipe.  Run: python3 tests/run_parlimit.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = "fn dbl(x Int) Int = x * 2\nlim = 2\n"
def check(body):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(HEAD + body)
    r = subprocess.run([sys.executable, "-m", "moxie", "check", f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
fails = []
def chk(name, cond):
    print(("ok    " if cond else "FAIL  ") + name)
    if not cond: fails.append(name)
MSG = "needs `limit:` with a constant number"
for form, want in (("println(par_map(dbl, List(1, 2), limit: 2))", True), ("println(List(1, 2) |> par_map(dbl, limit: 2))", True),
                   ("println(List(1, 2) |> par_map(dbl, limit: lim))", True), ("println(List(1, 2) |> par_map(dbl))", False),
                   ("println(par_map(dbl, List(1, 2)))", False), ("n = len(args) + 1\nprintln(List(1, 2) |> par_map(dbl, limit: n))", False),
                   ("println(List(1, 2) |> par_map(dbl, limit: 0))", False)):
    rc, o = check(form + "\n")
    chk(("accepts " if want else "rejects ") + form.splitlines()[-1], (rc == 0) if want else (rc != 0 and MSG in o))
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
