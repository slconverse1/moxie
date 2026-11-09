"""Data paths as first-class values: passed, returned, stored, composed, and updated through.  Run: python3 tests/run_paths.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA = '''tuple Address:
  city: String
tuple Firm:
  name: String,
  address: Address
tuple User:
  firm: Firm
u = User(firm: Firm(name: "Acme", address: Address(city: "Reno")))
'''

# (name, source, how, text): how is "run" (exit 0 and text in output) or "fail" (nonzero exit and text in output)
CASES = [
 ("a three-level path is passed to a function and read through",
  DATA + 'fn read_with(x: User, get: (User) -> String) String:\n  get(x)\nprintln(read_with(u, /User/firm/address/city))\n', "run", "Reno"),
 ("a path is bound to a name and called",
  DATA + 'city = /User/firm/address/city\nprintln(city(u))\nprintln(u |> city)\n', "run", "Reno\nReno"),
 ("replace works through a path parameter",
  DATA + 'fn set_to(x: User, p: (User) -> String, v: String) User:\n  replace(x, p, v)\nprintln(set_to(u, /User/firm/address/city, "Elko"))\n', "run", 'city: "Elko"'),
 ("modify works through a path parameter",
  DATA + 'fn bump(x: User, p: (User) -> String, f: (String) -> String) User:\n  modify(x, p, f)\nprintln(bump(u, /User/firm/name, (s): s + "!"))\n', "run", 'name: "Acme!"'),
 ("a function can return a path",
  DATA + 'fn pick(flag: Bool) (User) -> String:\n  if flag: /User/firm/name else: /User/firm/address/city\nprintln(pick(true)(u))\nprintln(pick(false)(u))\n', "run", "Acme\nReno"),
 ("paths can be held in a List and a Dict",
  DATA + 'paths = List(/User/firm/name, /User/firm/address/city)\nprintln(paths |> map((p): p(u)) |> collect())\ntable = Dict("n": /User/firm/name)\nwhen table("n"):\n  Ok(p) -> println(p(u))\n  Err(e) -> println("missing")\n', "run", 'List("Acme", "Reno")\nAcme'),
 ("paths compose with ~>",
  DATA + 'loc = /User/firm ~> /Firm/address ~> /Address/city\nprintln(loc(u))\n', "run", "Reno"),
]

fails = []
for name, src, how, word in CASES:
    for gc in (False, True):
        if how == "nogc-fail" and gc:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        want_fail = how in ("fail", "nogc-fail")
        ok = ((r.returncode != 0) if want_fail else (r.returncode == 0)) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:300]}"))
        if not ok:
            fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
