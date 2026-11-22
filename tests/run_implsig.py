"""An `impl` member may leave out the parameter types and result type its interface fixes.  Run: python3 tests/run_implsig.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
LOG = 'interface Logger\n  fn info(self, msg String) Unit\n  fn error(self, msg String) Unit\ntuple C deriving show\n  p String\n'
CASES = [
 ("types left out", LOG + 'impl Logger for C\n  fn info(self, msg)\n    println("${self.p} i $msg")\n  fn error(self, msg)\n    println("${self.p} E $msg")\nC(p: "a").info("x")\nC(p: "a").error("y")\n', 0, "a i x"),
 ("only the result left out", LOG + 'impl Logger for C\n  fn info(self, msg String)\n    println("i $msg")\n  fn error(self, msg String)\n    println("E $msg")\nC(p: "a").error("y")\n', 0, "E y"),
 ("written types still allowed", LOG + 'impl Logger for C\n  fn info(self, msg String) Unit\n    println("i $msg")\n  fn error(self, msg)\n    println("E $msg")\nC(p: "a").info("y")\n', 0, "i y"),
 ("the type is really the interface's", LOG + 'impl Logger for C\n  fn info(self, msg)\n    println(msg + 1)\n  fn error(self, msg)\n    ()\n', 2, "String"),
 ("a generic interface", 'interface Get[T]\n  fn get(self) T\n  fn add(self, n T) T\ntuple C deriving show\n  p String\nimpl Get[Int] for C\n  fn get(self)\n    len(self.p)\n  fn add(self, n)\n    n + 1\nprintln(C(p: "abc").get() + C(p: "").add(4))\n', 0, "8"),
 ("Self in the signature", 'interface Plus\n  fn plus(self, o Self) Self\ntuple V deriving show\n  x Int\nimpl Plus for V\n  fn plus(self, o)\n    V(x: self.x + o.x)\nprintln(V(x: 1).plus(V(x: 2)))\n', 0, "V(x: 3)"),
 ("an interface written without self", 'interface Shape\n  fn area() Int\ntuple Sq deriving show\n  s Int\nimpl Shape for Sq\n  fn area()\n    s * s\nprintln(Sq(s: 3).area())\n', 0, "9"),
 ("the built-in Show", 'tuple P deriving show\n  x Int\nimpl Show for P\n  fn show(self)\n    "P${self.x}"\nprintln(show(P(x: 3)))\n', 0, "P3"),
 ("the built-in Equatable and Ordered", 'tuple P deriving show\n  x Int\nimpl Equatable for P\n  fn ==(self, other)\n    self.x == other.x\nimpl Ordered for P\n  fn <(self, other)\n    self.x < other.x\nprintln(P(x: 1) == P(x: 1))\nprintln(P(x: 1) < P(x: 2))\n', 0, "true"),
 ("the built-in Addable", 'tuple M deriving show\n  n Int\nimpl Addable for M\n  fn +(self, other)\n    M(n: self.n + other.n)\n  static fn zero()\n    M(n: 0)\nprintln(M(n: 2) + M(n: 3))\n', 0, "M(n: 5)"),
 ("proxy still forwards", LOG + 'impl Logger for C\n  fn info(self, msg)\n    println("i $msg")\n  fn error(self, msg)\n    println("E $msg")\ntuple W deriving show\n  c C\nimpl Logger for W proxy(c)\n  fn info(self, msg)\n    self.c.info("w $msg")\nW(c: C(p: "a")).info("x")\nW(c: C(p: "a")).error("y")\n', 0, "i w x"),
 ("an ordinary function still needs its types", 'fn f(x)\n  x\n', 2, "no return type"),
 ("an inherent impl still needs its types", 'tuple P deriving show\n  x Int\nimpl P\n  fn twice(self)\n    self.x * 2\n', 2, "no return type"),
 ("a wrong written type is still an error", LOG + 'impl Logger for C\n  fn info(self, msg Int)\n    ()\n  fn error(self, msg)\n    ()\nC(p: "a").info("x")\n', 2, "mismatched"),
 ("an impl keeps the interface's parameter names", LOG + 'impl Logger for C\n  fn info(self, text)\n    println(text)\n  fn error(self, msg)\n    println(msg)\n', 2, "is called `msg` in interface"),
 ("a label works on the type and through the interface", LOG + 'impl Logger for C\n  fn info(self, msg)\n    println("i $msg")\n  fn error(self, msg)\n    println("E $msg")\nC(p: "a").info(msg: "x")\nC(p: "a").error(msg: "y")\n', 0, "E y"),
 ("a label that names no parameter", LOG + 'impl Logger for C\n  fn info(self, msg)\n    ()\n  fn error(self, msg)\n    ()\nC(p: "a").info(text: "x")\n', 2, "no parameter named `text`"),
 ("the receiver cannot be renamed", LOG + 'impl Logger for C\n  fn info(this, msg)\n    ()\n  fn error(self, msg)\n    ()\n', 2, "no return type"),
 ("a renamed parameter with the type written is an error too", LOG + 'impl Logger for C\n  fn info(self, text String) Unit\n    ()\n  fn error(self, msg)\n    ()\n', 2, "is called `msg`"),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        p = os.path.join(D, "t.mxi")
        open(p, "w").write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", p], cwd=ROOT, capture_output=True, text=True)
        o = r.stdout + r.stderr
        good = ((r.returncode != 0) if rc_want == 2 else (r.returncode == 0)) and word in o
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={r.returncode} {o.strip()[:300]!r}"))
        if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
