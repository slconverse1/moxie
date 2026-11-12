"""Secret[T].  Run: python3 tests/run_secret.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []

def run(src, cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    return r.returncode, r.stdout.decode() + r.stderr.decode()

def chk(name, src, rc_want, *wants, absent=(), cmd="run"):
    rc, out = run(src, cmd)
    ok = rc == rc_want and all(w in out for w in wants) and not any(a in out for a in absent)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
    if not ok: fails.append(name)

T = 'token: Secret[String] = secret("hunter2")\n'
chk("println shows no secret", T + 'println(token)\n', 0, "Secret(***)", absent=("hunter2",))
chk("interpolation shows no secret", T + 'println("token is ${token}")\n', 0, "token is Secret(***)", absent=("hunter2",))
chk("show shows no secret", T + 'println(show(token))\n', 0, "Secret(***)", absent=("hunter2",))
chk("dbg shows no secret", T + 'x = dbg(token)\n', 0, "Secret(***)", absent=("hunter2",))
chk("a secret inside a tuple or list stays hidden", T + 'println(List(token))\nprintln((1, token))\n', 0, "List(Secret(***))", "(1, Secret(***))", absent=("hunter2",))
chk("reveal gives the value", T + 'println(reveal(token))\n', 0, "hunter2")
chk("secret_eq compares", T + 'println(secret_eq(token, secret("hunter2")))\nprintln(secret_eq(token, secret("x")))\n', 0, "true\nfalse")
chk("== is a compile error", T + 'u = secret("x")\nprintln(token == u)\n', 1, "can't be compared with ==", cmd="check")
chk("== aborts at run time when the type is hidden", 'fn eq[T: Equatable](a: T, b: T) Bool\n  a == b\nprintln(eq(secret("a"), secret("a")))\n', 1, "use secret_eq")
chk("a Secret is not a String", 'fn f(s: String) Int\n  len(s)\nprintln(f(secret("x")))\n', 1, "mismatched types", cmd="check")
chk("a String is not a Secret", 'fn f(s: Secret[String]) Bool\n  secret_eq(s, s)\nprintln(f("x"))\n', 1, "mismatched types", cmd="check")
chk("a Secret is not a Dict key", 'd = Dict(1: secret("a"))\nk = secret("a")\nprintln(Set(k))\n', 1, "can't be a Dict key or Set member")
chk("a Secret can be sent over a channel", 'rx, tx = Chan[Secret[String]][1]()\n_ = write(tx, secret("pw"))\nr = read(rx)?\nprintln(r)\nprintln(reveal(r))\n', 0, "Secret(***)\npw")
chk("secret of a secret is the same secret", 'a = secret("x")\nb = secret(a)\nprintln(reveal(b))\n', 0, "x")
print()
print("FAILURES: " + ", ".join(fails) if fails else "all secret tests passed")
sys.exit(1 if fails else 0)
