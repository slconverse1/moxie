"""Foreign function tests (libm, libc, zlib).  Run: python3 tests/run_ffi.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, *flags, cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr

HDR = '''tuple DivT:
  quot: Int32
  rem: Int32
foreign "z":
  pure fn crc32(crc: UInt32, data: Array[Byte], len: UInt32 = len(data)) UInt32
foreign "m":
  pure fn cos(x: Double) Double
  pure fn pow(x: Double, y: Double) Double
  pure fn frexp(x: Double, ref exp: Int32) Double
foreign "c":
  pure fn div(a: Int32, b: Int32) DivT
  pure fn strlen(s: CString) UInt
  pure fn atoi(s: CString) Int32
'''
CASES = [
 ("doubles", 'println("${cos(0.0)} ${pow(2.0, 10.0)}")\n', 0, "1.0 1024.0"),
 ("byte array with a length parameter filled in", 'println("${crc32(0u32, b"hello")}")\n', 0, "907060870"),
 ("ref out-parameter", 'e = 0i32\nm = frexp(8.0, ref e)\nprintln("$m $e")\n', 0, "0.5 4"),
 ("struct returned by value", 'println("${div(17i32, 5i32)}")\n', 0, "DivT(quot: 3, rem: 2)"),
 ("CString", 'println("${strlen(cstr("héllo"))} ${atoi(cstr("42"))}")\n', 0, "6 42"),
 ("CString needs cstr", 'println("${strlen("abc")}")\n', 1, "cstr"),
 ("a foreign result is an ordinary value", 'xs = List(1.0, 4.0, 9.0)\nprintln("${xs |> to_stream() |> map(pow(_, 0.5)) |> collect()}")\n', 0, "List(1.0, 2.0, 3.0)"),
 ("foreign function without an effect declaration is an error", 'foreign "m":\n  fn sin(x: Double) Double\nprintln("x")\n', 2, "needs an effect declaration"),
 ("pure fn may not call an impure foreign function", 'foreign "m":\n  impure fn sin(x: Double) Double\npure fn f(x: Double) Double: sin(x)\n', 2, "pure fn"),
 ("unknown function in a library", 'foreign "m":\n  pure fn no_such_function(x: Double) Double\nprintln("x")\n', 1, "has no function"),
 ("unknown library", 'foreign "no_such_lib_xyz":\n  pure fn f(x: Double) Double\nprintln("x")\n', 1, "cannot load native library"),
 ("a body is not allowed", 'foreign "m":\n  pure fn cos(x: Double) Double: x\n', 2, "no body"),
]
fails = []
for name, body, rc_want, word in CASES:
    src = HDR + body if not body.startswith("foreign") else body
    cmd = "check" if rc_want == 2 else "run"
    rc, o = run(src, cmd=cmd)
    good = (rc == rc_want or (rc_want == 2 and rc != 0)) and word in o
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {o.strip()[:150]}"))
    if not good: fails.append(name)
SLOW = 'foreign "c":\n  parks fn usleep(us: UInt32) Int32\nfn slow(tx: ChanW[Int]) Unit:\n  usleep(300000u32)\n  \\write(tx, 1)\nfn ticker(tx: ChanW[Int]) Unit:\n  for i in 1..=3:\n    \\write(tx, i * 10)\nrx, tx = Chan[Int][8]()\nrx2, tx2 = Chan[Int][8]()\nrun slow(tx)\nrun ticker(tx2)\nprintln(read(rx2)?)\nprintln(read(rx2)?)\nprintln(read(rx2)?)\nprintln(read(rx)?)\n'
import time
t0 = time.time()
rc, o = run(SLOW)
good = rc == 0 and o.split() == ["10", "20", "30", "1"]
print(("ok    " if good else "FAIL  ") + "a parks foreign function lets other fibers run")
if not good: fails.append("parks thread")
rc, o = run(HDR + 'println("${crc32(0u32, b"hello")}")\n', "--gc")
print(("ok    " if rc == 0 and "907060870" in o else "FAIL  ") + "moxie/gc mode")
if not (rc == 0 and "907060870" in o): fails.append("gc")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
