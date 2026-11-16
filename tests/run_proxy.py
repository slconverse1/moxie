"""`impl Iface for T proxy(field)`: the interface's other methods forward to the field.  Run: python3 tests/run_proxy.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, cmd="run", gc=False):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + [cmd, f.name], cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
B = 'interface Shape\n  fn area() Int,\n  fn name() String\ntuple Sq\n  s Int\nimpl Shape for Sq\n  fn area() Int\n    s * s\n  fn name() String\n    "sq"\n'
OK = [
 ("every method forwards", B + 'tuple W\n  inner Sq\nimpl Shape for W proxy(inner)\nw = W(inner: Sq(s: 3))\nprintln(w.area())\nprintln(w.name())\n', "9\nsq\n"),
 ("one method is written, the rest forward", B + 'tuple W\n  inner Sq\nimpl Shape for W proxy(inner)\n  fn name() String\n    "wrapped ${inner.name()}"\nw = W(inner: Sq(s: 3))\nprintln(w.area())\nprintln(w.name())\n', "9\nwrapped sq\n"),
 ("the held value can be any Shape", B + 'tuple W\n  inner any Shape\nimpl Shape for W proxy(inner)\nprintln(W(inner: Sq(s: 4)).area())\n', "16\n"),
 ("the proxy is a Shape where one is wanted", B + 'tuple W\n  inner Sq\nimpl Shape for W proxy(inner)\nfn show(x any Shape) String = "${x.name()} ${x.area()}"\nprintln(show(W(inner: Sq(s: 2))))\n', "sq 4\n"),
 ("a generic interface", 'interface Get[T]\n  fn get() T\ntuple A\n  v Int\nimpl Get[Int] for A\n  fn get() Int\n    v\ntuple W\n  a A\nimpl Get[Int] for W proxy(a)\nprintln(W(a: A(v: 7)).get())\n', "7\n"),
 ("methods with arguments", 'interface Add\n  fn plus(a Int, b Int) Int\ntuple C\n  k Int\nimpl Add for C\n  fn plus(a Int, b Int) Int\n    a + b + k\ntuple W\n  c C\nimpl Add for W proxy(c)\nprintln(W(c: C(k: 10)).plus(1, 2))\n', "13\n"),
 ("an interface written with explicit self", 'interface Logger\n  fn info(self, msg String) String\n  fn error(self, msg String) String\ntuple C\n  p String\nimpl Logger for C\n  fn info(self, msg String) String\n    "${self.p} i $msg"\n  fn error(self, msg String) String\n    "${self.p} E $msg"\ntuple W\n  c C\nimpl Logger for W proxy(c)\n  fn info(self, msg String) String\n    "stamped ${self.c.info(msg)}"\nw = W(c: C(p: "a"))\nprintln(w.info("x"))\nprintln(w.error("y"))\n', "stamped a i x\na E y\n"),
 ("a built-in interface", 'tuple Dog\n  name String\nimpl Show for Dog\n  fn show(self) String\n    "Dog ${self.name}"\ntuple Pet\n  dog Dog\nimpl Show for Pet proxy(dog)\nprintln(Pet(dog: Dog(name: "Rex")).show())\n', "Dog Rex\n"),
 ("a name that is not a keyword elsewhere", 'proxy = 3\nprintln(proxy)\n', "3\n"),
]
ERR = [
 ("a field that does not exist", B + 'tuple W\n  inner Sq\nimpl Shape for W proxy(nope)\n', "has no field `nope`; its fields are `inner`"),
 ("a field that does not implement it", B + 'tuple P\n  n Int\ntuple W\n  p P\nimpl Shape for W proxy(p)\n', "nothing to forward to"),
 ("a static member", 'interface Mk\n  static fn make() Int,\n  fn id() Int\ntuple X\n  n Int\nimpl Mk for X\n  static fn make() Int\n    1\n  fn id() Int\n    n\ntuple Y\n  x X\nimpl Mk for Y proxy(x)\n', "it is a `static` member"),
 ("Self in a signature", 'interface Cmp\n  fn same(other Self) Bool\ntuple X\n  n Int\nimpl Cmp for X\n  fn same(other Self) Bool\n    n == other.n\ntuple Y\n  x X\nimpl Cmp for Y proxy(x)\n', "`Self` in its signature"),
 ("an interface not declared here", 'tuple X\n  n Int\ntuple Y\n  x X\nimpl Frob for Y proxy(x)\n', "needs the declaration of `Frob`"),
 ("a built-in interface needs the field to implement it", 'tuple X\n  n Int\ntuple Y\n  x X\nimpl Show for Y proxy(x)\n', "no `impl Show for X`"),
 ("a built-in interface with Self in a signature", 'tuple A\n  n Int\nimpl Equatable for A\n  fn ==(self, other Self) Bool\n    n == other.n\ntuple B\n  a A\nimpl Equatable for B proxy(a)\n', "`Self` in its signature"),
 ("no interface in the header", 'tuple X\n  n Int\nimpl X proxy(n)\n', "goes in an `impl Interface for Type` header"),
]
fails = []
for name, src, want in OK:
    for gc in (False, True):
        rc, out = run(src, "run", gc)
        good = rc == 0 and out == want
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
        if not good:
            fails.append(name)
for name, src, word in ERR:
    rc, out = run(src, "check")
    good = rc != 0 and word in out
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
    if not good:
        fails.append(name)

# an interface declared in an imported package
PKG = "export interface Shape\n  fn area() Int,\n  fn name() String\nexport tuple Sq\n  s Int\nimpl Shape for Sq\n  fn area() Int\n    s * s\n  fn name() String\n    \"sq\"\n"
PKG_CASES = [
 ("an interface from an imported package", "import shapes\ntuple W\n  inner shapes.Sq\nimpl shapes.Shape for W proxy(inner)\nw = W(inner: shapes.Sq(s: 3))\nprintln(w.area())\nprintln(w.name())\n", "9\nsq\n"),
 ("an imported interface with one method written", "import shapes\ntuple W\n  inner shapes.Sq\nimpl shapes.Shape for W proxy(inner)\n  fn name() String\n    \"wrapped\"\nw = W(inner: shapes.Sq(s: 3))\nprintln(w.area())\nprintln(w.name())\n", "9\nwrapped\n"),
 ("an interface imported by name", "import shapes (Shape, Sq)\ntuple W\n  inner Sq\nimpl Shape for W proxy(inner)\nprintln(W(inner: Sq(s: 4)).area())\n", "16\n"),
]
for name, src, want in PKG_CASES:
    for gc in (False, True):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "shapes.mxi"), "w").write(PKG)
            f = os.path.join(d, "main.mxi")
            open(f, "w").write(src)
            r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f], cwd=ROOT, capture_output=True, text=True, timeout=120)
        out = r.stdout + r.stderr
        good = r.returncode == 0 and out == want
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={r.returncode} {out.strip()[:300]!r}"))
        if not good:
            fails.append(name)
sys.exit(1 if fails else 0)
