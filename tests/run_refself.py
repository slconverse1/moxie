"""A method that declares `ref self` changes the variable it is called on, and the call says so: `ref m.add(1)`.  Run: python3 tests/run_refself.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM = '''tuple Mem deriving show
  data List[Int]
impl Mem
  fn add(ref self, x Int) Unit
    self = Mem(data: self.data + x)
  fn total(self) Int = sum(self.data)
m = Mem(data: List())
'''
IFACE = '''interface Sink
  fn put(ref self, x Int) Unit
tuple Mem deriving show
  data List[Int]
impl Sink for Mem
  fn put(ref self, x Int) Unit
    self = Mem(data: self.data + x)
fn fill[S Sink](ref s S, n Int) Unit
  for i in 1..n
    ref s.put(i)
fn bump(ref m Mem) Unit
  ref m.put(100)
m = Mem(data: List())
'''
CASES = [
 ("a ref self method changes its receiver", MEM + "ref m.add(1)\nref m.add(2)\nprintln(m)\nprintln(m.total())\n", 0, "Mem(data: List(1, 2))\n3"),
 ("the receiver is changed in a loop", MEM + "for i in 1..3\n  ref m.add(i)\nprintln(m.total())\n", 0, "6"),
 ("a call without ref is an error", MEM + "m.add(1)\n", 2, "changes its receiver: write `ref m.add(...)`"),
 ("ref on a method that does not take ref self is an error", MEM + "println(ref m.total())\n", 2, "does not take `ref self`"),
 ("through an interface and a generic function", IFACE + "fill(ref m, 3)\nbump(ref m)\nprintln(m)\n", 0, "Mem(data: List(1, 2, 3, 100))"),
 ("ref before a call on a field is an error", MEM + "t = (inner: m)\nref t.inner.add(1)\n", 2, "goes with a call on a name"),
 ("an ordinary method still cannot change its receiver", MEM.replace("fn total(self) Int = sum(self.data)", "fn total(self) Int = sum(self.data)") + "println(m.total())\nprintln(m)\n", 0, "0\nMem(data: List())"),
]
fails = []
for name, src, rc, want in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name], cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = (r.stdout + r.stderr).strip()
        if rc is None:
            ok = r.returncode != 0
        elif rc == 0:
            ok = r.returncode == 0 and o == want
        else:
            ok = r.returncode != 0 and want in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
