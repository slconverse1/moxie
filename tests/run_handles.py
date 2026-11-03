"""FFI handle tests: a small C library is compiled on the fly.  Run: python3 tests/run_handles.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
C = r'''
#include <stdlib.h>
#include <stdio.h>
typedef struct { int n; } counter;
counter *counter_open(int start) { if (start < 0) return NULL; counter *c = malloc(sizeof *c); c->n = start; return c; }
int counter_bump(counter *c) { return ++c->n; }
int counter_close(counter *c) { printf("closed\n"); fflush(stdout); free(c); return 0; }
'''
open(os.path.join(D, "cnt.c"), "w").write(C)
subprocess.check_call(["gcc", "-shared", "-fPIC", "-o", os.path.join(D, "libcnt.so"), os.path.join(D, "cnt.c")])

def run(src, *flags, cmd="run"):
    p = os.path.join(D, "t.mxi")
    open(p, "w").write(src)
    env = dict(os.environ, MOXIE_NATIVE_PATH=D)
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, p], cwd=ROOT, capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr

HDR = '''foreign "cnt":
  handle Counter closes counter_close
  impure fn counter_open(start: Int32) Result[Counter, Error]
  impure fn counter_bump(c: Counter) Int32
  impure fn counter_close(c: Counter) Int32
'''
CASES = [
 ("open, use, close", 'c = counter_open(5)?\nprintln(counter_bump(c))\ncounter_close(c)\nprintln("done")\n', 0, "6\nclosed\ndone"),
 ("NULL becomes Err", 'when counter_open(-1):\n  Ok(c) -> println("opened")\n  Err(e) -> println("failed ${e.message}")\n', 0, "failed counter_open returned NULL"),
 ("use after close is a compile error", 'c = counter_open(1)?\ncounter_close(c)\nprintln(counter_bump(c))\n', 2, "use of moved value"),
 ("move into close", 'c = counter_open(1)?\ncounter_close(move c)\nprintln("ok")\n', 0, "closed\nok"),
 ("copying a handle needs move", 'c = counter_open(1)?\nd = c\ncounter_close(move d)\n', 2, "is a resource"),
 ("a handle left open is closed at exit", 'c = counter_open(1)?\nprintln(counter_bump(c))\n', 0, "2\nclosed"),
 ("close builtin", 'c = counter_open(1)?\nclose(c)\nprintln("x")\n', 0, "closed\nx"),
 ("closer missing", 'foreign "cnt":\n  handle Counter closes nope\n  impure fn counter_bump(c: Counter) Int32\nprintln("x")\n', 1, "closing function"),
]
LIBC = '''foreign "c":
  handle File closes fclose
  impure fn fopen(path: CString, mode: CString) Result[File, Error]
  impure fn fputs(s: CString, f: File) Int32
  impure fn fclose(f: File) Int32
f = fopen(cstr("%s/out.txt"), cstr("w"))?
fputs(cstr("hello"), f)
fclose(move f)
println("wrote")
''' % D
CASES.append(("libc fopen/fclose", LIBC, 0, "wrote"))
fails = []
for name, body, rc_want, word in CASES:
    src = body if body.startswith("foreign") else HDR + body
    cmd = "check" if rc_want == 2 else "run"
    rc, o = run(src, cmd=cmd)
    good = (rc == rc_want or (rc_want == 2 and rc != 0)) and word in o
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {o.strip()[:200]}"))
    if not good: fails.append(name)
rc, o = run(HDR + 'c = counter_open(1)?\nprintln(counter_bump(c))\ncounter_close(c)\n', "--gc")
good = rc == 0 and "closed" in o
print(("ok    " if good else "FAIL  ") + "moxie/gc mode")
if not good: fails.append("gc")
ok = open(os.path.join(D, "out.txt")).read() == "hello" if os.path.exists(os.path.join(D, "out.txt")) else False
print(("ok    " if ok else "FAIL  ") + "the file was written and closed")
if not ok: fails.append("file")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
