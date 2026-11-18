"""User types with `to_stream()` are pipeline sources.  Run: python3 tests/run_iterable.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    return r.returncode, r.stdout.decode() + r.stderr.decode()

SRC = """tuple Countdown
  from Int

impl Countdown
  fn to_stream(self) Stream[Int] = (1..self.from) |> reverse()

c = Countdown(3)
"""
fails = []
def chk(name, body, rc_want, *wants, cmd="run"):
    rc, out = run(SRC + body, cmd)
    ok = rc == rc_want and all(w in out for w in wants)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
    if not ok:
        fails.append(name)

chk("map", "println(c |> map((x) -> x * 2) |> collect())\n", 0, "List(6, 4, 2)")
chk("filter+sum", "println(c |> filter((x) -> x > 1) |> sum())\n", 0, "5")
chk("for", "for x in c\n  println(x)\n", 0, "3\n2\n1")
chk("element type flows", "bad = c |> map((s) -> s + \"x\") |> collect()\n", 1, "cannot apply `+`", cmd="check")
sys.exit(1 if fails else 0)
