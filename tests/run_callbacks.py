"""FFI callback tests: a small C library is compiled on the fly.  Run: python3 tests/run_callbacks.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
C = r'''
typedef struct { double x; double y; } pt;
double apply_n(double (*f)(double), double x, int n) { for (int i = 0; i < n; i++) x = f(x); return x; }
int count_if(int (*pred)(int), int lo, int hi) { int c = 0; for (int i = lo; i < hi; i++) if (pred(i)) c++; return c; }
double combine(double (*f)(pt), double a, double b) { pt p = {a, b}; return f(p); }
void for_each(int n, void (*cb)(int, void *), void *ud) { for (int i = 0; i < n; i++) cb(i * i, ud); }
long chunks(const unsigned char *buf, unsigned long n, long (*cb)(const unsigned char *, unsigned long, void *), void *ud) {
  long total = 0; unsigned long half = n / 2;
  total += cb(buf, half, ud); total += cb(buf + half, n - half, ud); return total; }
double sum_d(const double *p, unsigned long n) { double t = 0; for (unsigned long i = 0; i < n; i++) t += p[i]; return t; }
void scale_i(int *p, unsigned long n, int k) { for (unsigned long i = 0; i < n; i++) p[i] *= k; }
int rows(const int *a, unsigned long n, int (*cb)(const int *, unsigned long)) { int t = 0; for (unsigned long i = 0; i + 2 <= n; i += 2) t += cb(a + i, 2); return t; }
void sort_d(double *a, unsigned long n, unsigned long sz, int (*cmp)(const double *, const double *)) {
  for (unsigned long i = 1; i < n; i++) for (unsigned long j = i; j > 0 && cmp(a + j - 1, a + j) > 0; j--) { double t = a[j]; a[j] = a[j-1]; a[j-1] = t; } }
'''
open(os.path.join(D, "cb.c"), "w").write(C)
subprocess.check_call(["gcc", "-shared", "-fPIC", "-o", os.path.join(D, "libcb.so"), os.path.join(D, "cb.c")])
EVC = r'''
#include <pthread.h>
#include <unistd.h>
typedef void (*cb_t)(int, double);
static cb_t g_cb; static pthread_t th; static int g_n;
static void *run(void *a) { for (int i = 0; i < g_n; i++) { g_cb(i, i * 1.5); usleep(1000); } return 0; }
void ev_start(cb_t cb, int n) { g_cb = cb; g_n = n; pthread_create(&th, 0, run, 0); }
void ev_finish(void) { pthread_join(th, 0); }
'''
open(os.path.join(D, "ev.c"), "w").write(EVC)
subprocess.check_call(["gcc", "-shared", "-fPIC", "-pthread", "-o", os.path.join(D, "libev.so"), os.path.join(D, "ev.c")])
HC = r'''
#include <pthread.h>
typedef int (*h_t)(int);
static h_t g; static pthread_t th; static int gn; static long total;
static void *run(void *a) { for (int i = 0; i < gn; i++) total += g(i); return 0; }
void h_start(h_t cb, int n) { g = cb; gn = n; total = 0; pthread_create(&th, 0, run, 0); }
long h_wait(void) { pthread_join(th, 0); return total; }
int h_now(h_t cb, int x) { return cb(x); }
'''
open(os.path.join(D, "hd.c"), "w").write(HC)
subprocess.check_call(["gcc", "-shared", "-fPIC", "-pthread", "-o", os.path.join(D, "libhd.so"), os.path.join(D, "hd.c")])
HDR = '''tuple Pt:
  x: Double
  y: Double
foreign "cb":
  pure fn apply_n(f: (Double) -> Double, x: Double, n: Int32) Double
  pure fn count_if(pred: (Int32) -> Int32, lo: Int32, hi: Int32) Int32
  pure fn combine(f: (Pt) -> Double, a: Double, b: Double) Double
  impure fn for_each(n: Int32, cb: (Int32, UserData) -> Unit, ud: UserData)
  impure fn chunks(buf: Array[Byte], n: UInt = len(buf), cb: (Array[Byte], UInt, UserData) -> Int64, ud: UserData) Int64
  pure fn sum_d(a: Array[Double], n: UInt = len(a)) Double
  impure fn scale_i(ref a: Array[Int32], n: UInt = len(a), k: Int32)
  impure fn rows(a: Array[Int32], n: UInt = len(a), cb: (Array[Int32], UInt) -> Int32) Int32
  impure fn sort_d(ref a: Array[Double], n: UInt = len(a), sz: UInt = size_of(a), cmp: (Ptr[Double], Ptr[Double]) -> Int32)
  parks fn slow(f: (Int32) -> Int32, n: Int32) Int32
'''
CASES = [
 ("a closure is called from C", 'println(apply_n((v): v * 2.0, 1.0, 10i32))\n', 0, "1024.0"),
 ("the closure sees captured values", 'k = 3.0\nprintln(apply_n((v): v + k, 0.0, 4i32))\n', 0, "12.0"),
 ("an integer predicate", 'println(count_if((v): if v % 3 == 0i32: 1i32 else: 0i32, 0i32, 10i32))\n', 0, "4"),
 ("a tuple argument", 'println(combine((p): p.x + p.y * 10.0, 1.0, 2.0))\n', 0, "21.0"),
 ("a function name works too", 'fn half(v: Double) Double: v / 2.0\nprintln(apply_n(half, 64.0, 3i32))\n', 0, "8.0"),
 ("user data is not passed to the closure", 'fn show(v: Int32) Unit:\n  println(v)\nfor_each(4i32, show)\n', 0, "0\n1\n4\n9"),
 ("a buffer arrives as one array", 'println(chunks(b"abcdefg", (d): len(d) * 10i64))\n', 0, "70"),
 ("the buffer holds the bytes C passed", 'fn show(d: Array[Byte]) Int64:\n  println(d)\n  0i64\nprintln(chunks(b"hi there", show))\n', 0, "Array(104, 105, 32, 116)\nArray(104, 101, 114, 101)"),
 ("a buffer callback may not park", 'fn bad(d: Array[Byte]) Int64:\n  sleep(1ms)\n  0i64\nprintln(chunks(b"abcd", bad))\n', 2, "may park"),
 ("an abort in the callback ends the program", 'println(count_if((v): 1i32 / (v - v), 0i32, 3i32))\nprintln("not reached")\n', 1, "abort"),
 ("a callback may not park", 'fn bad(v: Double) Double:\n  sleep(1ms)\n  v\nprintln(apply_n(bad, 1.0, 2i32))\n', 2, "may park"),
 ("a callback-taking function cannot be parks", 'foreign "cb":\n  parks fn apply_n(f: (Double) -> Double, x: Double, n: Int32) Double\n', 2, "callback"),
]
NUMCASES = [
 ("an array of doubles goes in", 'println(sum_d(Array(1.5, 2.5, 4.0)))\n', 0, "8.0"),
 ("a ref array of numbers is written back", 'xs = Array(1i32, 2i32, 3i32)\nscale_i(ref xs, 10i32)\nprintln(xs)\n', 0, "Array(10, 20, 30)"),
 ("an array and its length arrive in a callback", 'println(rows(Array(1i32, 2i32, 3i32, 4i32, 5i32, 6i32), (r): r(0) * r(1)))\n', 0, "44"),
 ("Ptr[T] gives the callback the number", 'xs = Array(3.5, 1.5, 2.5)\nsort_d(ref xs, (a, b): if a < b: -1i32 elif a > b: 1i32 else: 0i32)\nprintln(xs)\n', 0, "Array(1.5, 2.5, 3.5)"),
 ("size_of needs an array of numbers", 'foreign "cb":\n  impure fn sort_d(n: Int32, sz: UInt = size_of(n), cmp: (Ptr[Double], Ptr[Double]) -> Int32)\nsort_d(1i32, (a, b): 0i32)\n', 1, "size_of"),
]
EVH = '''foreign "ev":
  impure fn ev_start(cb: Events[(Int32, Double)], n: Int32)
  impure fn ev_finish()
'''
EVCASES = [
 ("a C thread's callbacks arrive as channel messages", EVH + 'rx, tx = Chan[(Int32, Double)][16]()\nev_start(move tx, 3i32)\nfor i in 1..=3:\n  println(read(rx)?)\nev_finish()\n', 0, "(0, 0.0)\n(1, 1.5)\n(2, 3.0)"),
 ("a waiting fiber is not a deadlock while events can come", EVH + 'fn consumer(rx: ChanR[(Int32, Double)], out: ChanW[Int]) Result[Unit, Error]:\n  for i in 1..=4:\n    r = read(rx)?\n    \\write(out, i)\n  Ok(())\nrx, tx = Chan[(Int32, Double)][2]()\ndone_r, done_w = Chan[Int][1]()\nrun consumer(rx, done_w)\nev_start(move tx, 4i32)\nfor i in 1..=4:\n  println(read(done_r)?)\nev_finish()\n', 0, "1\n2\n3\n4"),
 ("the library keeps the channel end, so move is required", EVH + 'rx, tx = Chan[(Int32, Double)][4]()\nev_start(tx, 1i32)\n', 2, "kept by the library"),
 ("a full channel drops events and says so", EVH + 'rx, tx = Chan[(Int32, Double)][1]()\nev_start(move tx, 50i32)\nev_finish()\nprintln(read(rx)?)\n', 0, "were dropped because the channel was full"),
]
HH = '''foreign "hd":
  impure fn h_start(cb: Handler[(Int32) -> Int32], n: Int32)
  parks fn h_wait() Int64
  impure fn h_now(cb: Handler[(Int32) -> Int32], x: Int32) Int32
'''
HCASES = [
 ("C answers from its own thread through a handler", HH + 'h_start((v): v * 2i32, 4i32)\nprintln(h_wait())\n', 0, "12"),
 ("a handler may park", HH + 'fn slow(v: Int32) Int32:\n  sleep(1ms)\n  v + 1i32\nh_start(slow, 3i32)\nprintln(h_wait())\n', 0, "6"),
 ("a handler sees captured values", HH + 'k = 5i32\nh_start((v): v + k, 3i32)\nprintln(h_wait())\n', 0, "18"),
 ("on the scheduler's thread a handler runs at once", HH + 'println(h_now((v): v * 3i32, 5i32))\n', 0, "15"),
 ("an abort in a handler ends the program", HH + 'h_start((v): 1i32 / (v - v), 2i32)\nprintln(h_wait())\n', 1, "abort"),
]
fails = []
for name, body, rc_want, word in CASES + NUMCASES + EVCASES + HCASES:
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
