"""A member that takes `Self`: a compile error on a named `any` value, a clear abort when the hidden types differ at run time,
and a normal call when the types match.  Run: python3 tests/run_anyself.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
IFACE = '''interface Combine:
  fn combine(self, other: Self) Self
  fn label(self) String
tuple A:
  n: Int
tuple B:
  s: String
impl Combine for A:
  fn combine(self, other: Self) Self:
    A(n: self.n + other.n)
  fn label(self) String:
    "A${self.n}"
impl Combine for B:
  fn combine(self, other: Self) Self:
    B(s: self.s + other.s)
  fn label(self) String:
    "B${self.s}"
'''

def case(name, body, rc_want, *wants):
    d = tempfile.mkdtemp(prefix="mxany")
    p = os.path.join(d, "t.mxi")
    open(p, "w").write(IFACE + body)
    r = subprocess.run([sys.executable, "-m", "moxie", p], cwd=ROOT, capture_output=True, text=True, timeout=120)
    out = r.stdout + r.stderr
    ok = r.returncode == rc_want and all(w in out for w in wants) and "has no field" not in out
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {r.returncode}) {out[:300]!r}"))
    if not ok:
        fails.append(name)

case("a named any value: compile error", 'fn f(a: any Combine, b: any Combine) Unit:\n  c = a.combine(b)\n', 2, "takes a `Self`")
case("list elements of different types: a clear abort", 'xs: List[any Combine] = List(A(n: 1), B(s: "x"))\nprintln(xs(0).combine(xs(1)).label())\n', 1, "same type as the receiver")
case("list elements of the same type work", 'xs: List[any Combine] = List(A(n: 1), A(n: 2))\nprintln(xs(0).combine(xs(1)).label())\n', 0, "A3")
case("a generic function works", 'fn g[T: Combine](a: T, b: T) String:\n  a.combine(b).label()\nprintln(g(A(n: 1), A(n: 2)))\n', 0, "A3")

print()
print("FAILURES: " + ", ".join(fails) if fails else "all any/Self tests passed")
sys.exit(1 if fails else 0)
