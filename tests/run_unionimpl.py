"""Open data types (Guide 24n): a method called on a `type union` value, or a bound met by one, needs every member to provide it.
Also the two-file extension: a new variant and a new operation in a second file, the first untouched.  Run: python3 tests/run_unionimpl.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
ARITH = '''export tuple Lit deriving show
  value Int
export tuple Add[E] deriving show
  left E
  right E
export interface Eval[E]
  fn eval(self, rec (E) -> Int) Int
impl[E] Eval[E] for Lit
  fn eval(self, rec (E) -> Int) Int
    self.value
impl[E] Eval[E] for Add[E]
  fn eval(self, rec (E) -> Int) Int
    rec(self.left) + rec(self.right)
'''
MUL = '''tuple Mul[E] deriving show
  left E
  right E
impl[E] arith.Eval[E] for Mul[E]
  fn eval(self, rec (E) -> Int) Int
    rec(self.left) * rec(self.right)
'''
PRETTY = '''interface Pretty[E]
  fn pretty(self, rec (E) -> String) String
impl[E] Pretty[E] for arith.Lit
  fn pretty(self, rec (E) -> String) String
    "${self.value}"
impl[E] Pretty[E] for arith.Add[E]
  fn pretty(self, rec (E) -> String) String
    "(${rec(self.left)} + ${rec(self.right)})"
'''
PRETTY_MUL = '''impl[E] Pretty[E] for Mul[E]
  fn pretty(self, rec (E) -> String) String
    "${rec(self.left)} * ${rec(self.right)}"
'''
UNION = "type union Full = arith.Lit | arith.Add[Full] | Mul[Full]\n"
VALUE = "f Full = Mul[Full](arith.Lit(3), arith.Add[Full](arith.Lit(1), arith.Lit(2)))\n"
RUN = [
 ("a new variant and a new operation from a second file",
  "import arith\n" + MUL + PRETTY + PRETTY_MUL + UNION + "fn eval_full(e Full) Int\n  e.eval(eval_full)\nfn show_full(e Full) String\n  e.pretty(show_full)\n" + VALUE + "println(eval_full(f))\nprintln(show_full(f))\n",
  "9\n3 * (1 + 2)"),
 ("one generic function for every union",
  "import arith\n" + MUL + UNION + "fn eval_any[U arith.Eval[U]](e U) Int\n  e.eval(eval_any)\n" + VALUE + "println(eval_any(f))\n", "9"),
]
CHECK = [
 ("a member without the method is an error", "import arith\n" + MUL + PRETTY + UNION + "fn show_full(e Full) String\n  e.pretty(show_full)\n", "has no method `pretty`"),
 ("a member that doesn't meet a bound is an error", "import arith\n" + MUL + PRETTY + UNION + "fn go[U Pretty[U]](e U) String\n  e.pretty(go)\n" + VALUE + "println(go(f))\n", "doesn't implement `Pretty`"),
 ("all members have it: fine", "import arith\n" + MUL + PRETTY + PRETTY_MUL + UNION + "fn show_full(e Full) String\n  e.pretty(show_full)\n", None),
 ("a local union with a member lacking the method", "tuple A\n  n Int\ntuple B\n  n Int\ninterface Name\n  fn name(self) String\nimpl Name for A\n  fn name(self) String\n    \"a\"\ntype union AB = A | B\nfn f(x AB) String\n  x.name()\n", "`B`, which has no method `name`"),
 ("a local union where all have it", "tuple A\n  n Int\ntuple B\n  n Int\ninterface Name\n  fn name(self) String\nimpl Name for A\n  fn name(self) String\n    \"a\"\nimpl Name for B\n  fn name(self) String\n    \"b\"\ntype union AB = A | B\nfn f(x AB) String\n  x.name()\n", None),
]
fails = []
def run_in(files, cmd, gc=False):
    with tempfile.TemporaryDirectory() as d:
        for name, text in files.items():
            open(os.path.join(d, name), "w").write(text)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + [cmd, os.path.join(d, "main.mxi")], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()
for name, src, want in RUN:
    for gc in (False, True):
        rc, o = run_in({"arith.mxi": ARITH, "main.mxi": src}, "run", gc)
        ok = rc == 0 and o == want
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={rc} {o[:240]}"))
        if not ok: fails.append(name)
for name, src, word in CHECK:
    rc, o = run_in({"arith.mxi": ARITH, "main.mxi": src}, "check")
    ok = (rc != 0 and word in o) if word else rc == 0
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> rc={rc} {o[:240]}"))
    if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
