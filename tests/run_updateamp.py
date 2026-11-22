"""`update` lines: commas between lines, `&` for the field's current value, and `do` without `->`.  Run: python3 tests/run_updateamp.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = 'tuple Limits deriving show\n  retries Int,\n  timeout Int\ntuple Cfg deriving show\n  host String\n  port Int\n  names List[String]\n  limits Limits\nbase = Cfg(host: "h", port: 80, names: List("a", "b"), limits: Limits(retries: 3, timeout: 30))\n'
CASES = [
 ('comma between lines, & for the current value', HEAD + 's = base.update\n  port: & + 1,\n  limits:\n    retries: & * 2\nprintln("${s.port} ${s.limits.retries} ${s.limits.timeout}")\n', 0, '81 6 30'),
 ('a comma after a nested block ends the nested entry', HEAD + 's = base.update\n  limits:\n    retries: 9,\n    timeout: & + 1,\n  host: "x"\nprintln("${s.limits.retries} ${s.limits.timeout} ${s.host}")\n', 0, '9 31 x'),
 ('a trailing comma on the last line is allowed', HEAD + 's = base.update\n  port: 1,\n  host: "y",\nprintln("${s.port} ${s.host}")\n', 0, '1 y'),
 ('a missing comma is an error', HEAD + 's = base.update\n  port: 1\n  host: "y"\n', 2, 'ends with a comma unless it is the last one'),
 ('& as a receiver', HEAD + 's = base.update\n  names: & + List("c")\nprintln(s.names)\n', 0, 'List("a", "b", "c")'),
 ('& as a pipe slot keeps its pipe meaning', 'tuple C deriving show\n  n Int\nfn add(a Int, b Int) Int\n  a * 10 + b\nc = C(n: 3)\nx = c.update\n  n: 5 |> add(&, 2)\nprintln(x.n)\n', 0, '52'),
 ('every right-hand side sees the original', 'tuple P deriving show\n  a Int,\n  b Int\np = P(a: 1, b: 2)\nq = p.update\n  a: b,\n  b: a\nprintln("${q.a} ${q.b}")\n', 0, '2 1'),
 ('do takes its block on the lines below', HEAD + 'label = base.do\n  "$host:$port"\nprintln(label)\n', 0, 'h:80'),
 ('do with an arrow is an error', HEAD + 'label = base.do -> "$host:$port"\n', 2, 'no `->`'),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        s = src
        if not gc:
            s = s.replace("names List[String]", "names List[String][4]")
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(s)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = ((r.returncode != 0) if rc_want == 2 else r.returncode == 0) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:220]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
