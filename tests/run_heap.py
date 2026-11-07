"""The moxie/gc heap limit, [memory] heap (Spec 3).  Run: python3 tests/run_heap.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
GROW = '''fn main() Unit:
  xs = List[Int]()
  for i in 0..40000:
    gimme.1.xs = xs + i
  println(len(xs))
main()
'''
GARBAGE = '''fn main() Unit:
  n = 0
  for i in 0..400:
    s = List(1, 2, 3) * 1000
    gimme.1.n = len(s)
  println(n)
main()
'''
FIBER = '''fn hold(done: ChanW[Int]) Unit:
  xs = List[Int]()
  for i in 0..40000:
    gimme.1.xs = xs + i
  \\write(done, len(xs))
rx, tx = Chan[Int][1]()
run hold(tx)
println(read(rx)?)
'''
SMALL = '''xs = List[Int]()
for i in 0..100:
  gimme.1.xs = xs + i
println(len(xs))
'''


def moxie(d, *args):
    r = subprocess.run([sys.executable, "-m", "moxie", *args], cwd=d, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT), timeout=120)
    return r.returncode, r.stdout + r.stderr


def project(src, manifest):
    d = tempfile.mkdtemp()
    open(os.path.join(d, "main.mxi"), "w").write(src)
    if manifest is not None:
        open(os.path.join(d, "Moxie.toml"), "w").write(manifest)
    return d


def chk(name, got, rc, *words):
    code, out = got
    good = code == rc and all(w in out for w in words)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={code} {out.strip()[:300]}"))
    if not good:
        fails.append(name)


M = '[memory]\nheap = "64KiB"\n'
chk("a growing list passes the limit and ends the program", moxie(project(GROW, M), "--gc", "run", "main.mxi"), 1,
    "out of memory", "[memory] heap", "List")
chk("the same program runs when the limit is large", moxie(project(GROW, '[memory]\nheap = "16MiB"\n'), "--gc", "run", "main.mxi"), 0, "40000")
chk("no limit, no check", moxie(project(GROW, None), "--gc", "run", "main.mxi"), 0, "40000")
chk("garbage that is dropped does not count", moxie(project(GARBAGE, '[memory]\nheap = "64KiB"\n'), "--gc", "run", "main.mxi"), 0, "3000")
chk("a fiber's data counts against the shared heap", moxie(project(FIBER, M), "--gc", "run", "main.mxi"), 1, "out of memory")
chk("a small program under a small limit", moxie(project(SMALL, '[memory]\nheap = "64KiB"\n'), "--gc", "run", "main.mxi"), 0, "100")
chk("a bad size is a manifest error", moxie(project(SMALL, '[memory]\nheap = "lots"\n'), "--gc", "run", "main.mxi"), 2, "[memory] heap must be a size")
chk("an unknown key is a manifest error", moxie(project(SMALL, '[memory]\nstack = 1\n'), "--gc", "run", "main.mxi"), 2, "unknown key 'stack' in [memory]")
chk("[memory] belongs to moxie/gc", moxie(project(SMALL, M), "run", "main.mxi"), 2, "belongs to moxie/gc")
chk("slice is accepted", moxie(project(SMALL, '[memory]\nslice = "2ms"\n'), "--gc", "run", "main.mxi"), 0, "100")
print("all passed" if not fails else f"{len(fails)} failed: {fails}")
sys.exit(1 if fails else 0)
