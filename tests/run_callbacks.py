"""FFI callback tests: a small C library is compiled on the fly.  Run: python3 tests/run_callbacks.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
C = r'''
typedef struct { double x; double y; } pt;
double apply_n(double (*f)(double), double x, int n) { for (int i = 0; i < n; i++) x = f(x); return x; }
int count_if(int (*pred)(int), int lo, int hi) { int c = 0; for (int i = lo; i < hi; i++) if (pred(i)) c++; return c; }
double combine(double (*f)(pt), double a, double b) { pt p = {a, b}; return f(p); }
'''
open(os.path.join(D, "cb.c"), "w").write(C)
subprocess.check_call(["gcc", "-shared", "-fPIC", "-o", os.path.join(D, "libcb.so"), os.path.join(D, "cb.c")])
HDR = '''tuple Pt:
  x: Double
  y: Double
foreign "cb":
  pure fn apply_n(f: (Double) -> Double, x: Double, n: Int32) Double
  pure fn count_if(pred: (Int32) -> Int32, lo: Int32, hi: Int32) Int32
  pure fn combine(f: (Pt) -> Double, a: Double, b: Double) Double
  parks fn slow(f: (Int32) -> Int32, n: Int32) Int32
'''
CASES = [
 ("a closure is called from C", 'println(apply_n(fn(v): v * 2.0, 1.0, 10i32))\n', 0, "1024.0"),
 ("the closure sees captured values", 'k = 3.0\nprintln(apply_n(fn(v): v + k, 0.0, 4i32))\n', 0, "12.0"),
 ("an integer predicate", 'println(count_if(fn(v): if v % 3 == 0i32: 1i32 else: 0i32, 0i32, 10i32))\n', 0, "4"),
 ("a tuple argument", 'println(combine(fn(p): p.x + p.y * 10.0, 1.0, 2.0))\n', 0, "21.0"),
 ("a function name works too", 'fn half(v: Double) Double: v / 2.0\nprintln(apply_n(half, 64.0, 3i32))\n', 0, "8.0"),
 ("an abort in the callback ends the program", 'println(count_if(fn(v): 1i32 / (v - v), 0i32, 3i32))\nprintln("not reached")\n', 1, "abort"),
 ("a callback may not park", 'fn bad(v: Double) Double:\n  sleep(1ms)\n  v\nprintln(apply_n(bad, 1.0, 2i32))\n', 2, "may park"),
 ("a callback-taking function cannot be parks", 'foreign "cb":\n  parks fn apply_n(f: (Double) -> Double, x: Double, n: Int32) Double\n', 2, "callback"),
]
fails = []
for name, body, rc_want, word in CASES:
    src = body if body.startswith("foreign") else HDR.replace("  parks fn slow(f: (Int32) -> Int32, n: Int32) Int32\n", "") + body
    p = os.path.join(D, "t.mxi")
    open(p, "w").write(src)
    cmd = "check" if rc_want == 2 else "run"
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, p], cwd=ROOT, capture_output=True, text=True,
                       env=dict(os.environ, MOXIE_NATIVE_PATH=D))
    o = r.stdout + r.stderr
    good = (r.returncode == rc_want or (rc_want == 2 and r.returncode != 0)) and word in o
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={r.returncode} {o.strip()[:200]}"))
    if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
