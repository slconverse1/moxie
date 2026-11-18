"""strip_prefix, strip_suffix, split_once.  Run: python3 tests/run_stropt.py"""
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
def chk(name, src, rc_want, *wants):
    for flags in ((), ("--gc",)):
        rc, out = run(src, flags)
        ok = rc == rc_want and all(w in out for w in wants)
        label = name + (" (gc)" if flags else "")
        print(("ok    " if ok else "FAIL  ") + label + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
        if not ok: fails.append(label)

chk("strip_prefix", 'println(strip_prefix("say hi", "say "))\nprintln(strip_prefix("quit", "say "))\nprintln(strip_prefix("say ", "say "))\n', 0, 'Some("hi")\nNone\nSome("")')
chk("strip_suffix", 'println(strip_suffix("a.txt", ".txt"))\nprintln(strip_suffix("a.txt", ".md"))\nprintln(strip_suffix(".txt", ".txt"))\n', 0, 'Some("a")\nNone\nSome("")')
chk("split_once splits at the first separator", 'println(split_once("a=b=c", "="))\nprintln(split_once("abc", "="))\nprintln(split_once("=x", "="))\nprintln(split_once("k=", "="))\nprintln(split_once("x", ""))\n', 0, 'Some(("a", "b=c"))\nNone\nSome(("", "x"))\nSome(("k", ""))\nNone')
chk("non-ASCII text", 'println(strip_prefix("héllo wörld", "héllo "))\nprintln(strip_suffix("wörld ñ", " ñ"))\nprintln(split_once("a→b→c", "→"))\n', 0, 'Some("wörld")\nSome("wörld")\nSome(("a", "b→c"))')
chk("with let-else and is", '''Some(text) = strip_prefix("say hello", "say ") else "no"
println(text)
fn parse_email(raw String) Option[(String, String)]
  Some((user, domain)) = split_once(raw, "@") else None
  if len(user) > 0 and contains(domain, ".") then Some((user, domain)) else None
if parse_email("alex@example.com") is Some((user, domain))
  println("User: ${user}, Domain: ${domain}")
println(parse_email("@x.com"))
println(parse_email("nonsense"))
''', 0, "hello", "User: alex, Domain: example.com", "None\nNone")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
