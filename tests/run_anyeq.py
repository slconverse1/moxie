"""`any I` with `==`, `<`, and as a Set element or Dict key when `I` embeds Equatable, Ordered, or Hashable.  Run: python3 tests/run_anyeq.py"""
import subprocess, sys, os, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = "interface Voice:\n{embeds}  fn say() String\n\ntuple Dog deriving eq, ord, hash:\n  name: String\n\ntuple Cat deriving eq, ord, hash:\n  name: String\n\nimpl Voice for Dog:\n  fn say() String: \"woof\"\nimpl Voice for Cat:\n  fn say() String: \"meow\"\n\n"
E = "  Equatable\n  Ordered\n  Hashable\n"
CASES = [
 ("equal values of one type", E, 'a: any Voice = Dog("x")\nb: any Voice = Dog("x")\nprintln(a == b)\n', "true", None),
 ("different types are unequal", E, 'a: any Voice = Dog("x")\nc: any Voice = Cat("x")\nprintln(a == c)\n', "false", None),
 ("ordering works", E, 'a: any Voice = Dog("x")\nb: any Voice = Dog("y")\nprintln(a < b)\n', "true", None),
 ("different types order by type name", E, 'a: any Voice = Dog("x")\nc: any Voice = Cat("x")\nprintln(c < a)\nprintln(a < c)\n', "true\nfalse", None),
 ("a set of any", E, 'a: any Voice = Dog("x")\nc: any Voice = Cat("x")\nprintln(len(Set(a, c, a)))\n', "2", None),
 ("== without Equatable is an error", "", 'a: any Voice = Dog("x")\nprintln(a == a)\n', None, "needs the interface to embed `Equatable`"),
 ("< without Ordered is an error", "  Equatable\n", 'a: any Voice = Dog("x")\nprintln(a < a)\n', None, "embed `Ordered`"),
 ("Set element without Hashable is an error", "  Equatable\n", 'fn n(xs: Set[any Voice]) Int: len(xs)\n', None, "must embed `Hashable`"),
 ("a parameter typed any", E, 'fn same(a: any Voice, b: any Voice) Bool: a == b\nprintln(same(Dog("x"), Dog("x")))\n', "true", None),
]
fails = []
for name, emb, body, out_has, err_has in CASES:
    d = tempfile.mkdtemp()
    f = os.path.join(d, "t.mx")
    open(f, "w").write(HEAD.format(embeds=emb) + body)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", f], capture_output=True, text=True, cwd=ROOT, timeout=120)
    ok = (out_has is None or out_has in r.stdout) and (err_has is None or err_has in r.stdout + r.stderr) and "Traceback" not in r.stderr
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> {(r.stdout + r.stderr).strip()[-200:]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
