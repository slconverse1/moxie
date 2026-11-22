"""NonEmpty works both as methods and as the prelude functions of the same name.  Run: python3 tests/run_nonempty.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROG = '''ne = non_empty(List(3, 1, 2))?
println(ne.len())
println(len(ne))
println(ne.min())
println(min(ne))
println(max(ne))
println(ne |> map((x) -> x + 1))
println(map((x) -> x * 2, ne))
println(ne.reduce1((a, b) -> a + b))
println(ne.to_list())
println(non_empty(List(7))?.min() + 1)
tuple Box
  items List[Int]
impl Box
  fn len(self) Int = 99
println(len(Box(List(1))))
'''
with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
    f.write(PROG)
r = subprocess.run([sys.executable, "-m", "moxie", "run", f.name], cwd=ROOT, capture_output=True, text=True)
os.unlink(f.name)
want = ["3", "3", "1", "1", "3", "NonEmpty(head: 4, tail: List(2, 3))", "NonEmpty(head: 6, tail: List(2, 4))", "6",
        "List(3, 1, 2)", "8", "99"]
ok = r.returncode == 0 and r.stdout.split("\n")[:-1] == want
print(("ok    " if ok else "FAIL  ") + "NonEmpty methods and prelude-function forms")
if not ok: print(r.stdout, r.stderr)
sys.exit(0 if ok else 1)
