"""The hidden Item of an `any Container` value stays opaque: it can't escape as a concrete type.  Run: python3 tests/run_hiddentype.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=(), cmd="check"):
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
def chk(name, body, rc_want, *wants, cmd="check"):
    for flags in ((), ("--gc",)):
        rc, out = run(HEAD + body, flags, cmd)
        ok = rc == rc_want and all(w in out for w in wants)
        label = name + (" (gc)" if flags else "")
        print(("ok    " if ok else "FAIL  ") + label + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
        if not ok: fails.append(label)

HEAD = """interface Container
  type Item
  fn get(i Int) Result[Item, Error]
  fn put(x Item) Self
  fn size() Int
tuple Names deriving show
  xs List[String]
impl Container for Names
  type Item = String
  fn get(i Int) Result[String, Error]
    Ok(xs(i))
  fn put(x String) Names
    Names(xs + List(x))
  fn size() Int
    len(xs)
"""
chk("get_or with an Int on the hidden Item is an error", "fn f(c any Container) Int\n  c.get(0).get_or(0)\n", 1, "c.Item")
chk("arithmetic on the hidden Item after let-else", "fn f(c any Container) Int\n  Ok(x) = c.get(0) else 0\n  x + 1\n", 1, "its type is hidden")
chk("arithmetic on the hidden Item in a when arm", "fn f(c any Container) Int\n  when c.get(0)\n    Ok(x) -> x + 1\n    Err(_) -> 0\n", 1, "its type is hidden")
chk("returning the hidden Item as an Int", "fn f(c any Container) Int\n  Ok(x) = c.get(0) else 0\n  x\n", 1, "expected `Int`, found `c.Item`")
chk("returning the hidden Item as a String", "fn f(c any Container) String\n  when c.get(0)\n    Ok(x) -> x\n    Err(_) -> \"\"\n", 1, "found `c.Item`")
chk("the Items of two different any values do not mix", "fn f(a any Container, b any Container) Int\n  Ok(x) = b.get(0) else 0\n  d = a.put(x)\n  1\n", 1, "a.Item")
chk("passing the Item back to the same value is fine", "fn f(c any Container) Int\n  Ok(x) = c.get(0) else 0\n  d = c.put(x)\n  d.size()\nprintln(f(Names(List(\"a\"))))\n", 0, "ok")
chk("printing it and narrowing with is are fine", "c any Container = Names(List(\"x\"))\nprintln(c.get(0))\nif c is Names(xs)\n  println(xs)\n", 0, "Ok(\"x\")\nList(\"x\")", cmd="run")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
