"""moxie bindgen tests: generate from a small header, compile the C, call it.  Run: python3 tests/run_bindgen.py"""
import os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

HEADER = r'''/* A tiny library for testing bindgen. */
#define MINI_VERSION 3
typedef unsigned int mini_u32;
typedef struct mini_point { double x; double y; } mini_point;
typedef struct mini_ctx mini_ctx;
enum mini_mode { MINI_FAST = 0, MINI_SLOW = 1, MINI_SAFE = 5 };

/* Adds two numbers. */
int mini_add(int a, int b);
/* Checksum of a buffer. */
mini_u32 mini_sum(mini_u32 seed, const unsigned char *buf, unsigned long len);
double mini_dist(mini_point p, mini_point q);
mini_ctx *mini_open(const char *name);
void mini_close(mini_ctx *c);
int mini_hits(mini_ctx *c);
int mini_parse(const char *s, int *out);
int mini_printf(const char *fmt, ...);
int mini_fill(unsigned char *buf, unsigned long n);
int mini_bad(unsigned char *buf);
'''
CODE = r'''
#include <math.h>
#include <stdlib.h>
typedef unsigned int mini_u32;
typedef struct mini_point { double x; double y; } mini_point;
struct mini_ctx { int hits; };
typedef struct mini_ctx mini_ctx;
mini_ctx *mini_open(const char *name) { mini_ctx *c = malloc(sizeof *c); c->hits = name[0]; return c; }
int mini_hits(mini_ctx *c) { return ++c->hits; }
void mini_close(mini_ctx *c) { free(c); }
int mini_add(int a, int b) { return a + b; }
mini_u32 mini_sum(mini_u32 seed, const unsigned char *buf, unsigned long len) {
  mini_u32 s = seed; for (unsigned long i = 0; i < len; i++) s = s * 31u + buf[i]; return s; }
double mini_dist(mini_point p, mini_point q) { return sqrt((p.x-q.x)*(p.x-q.x) + (p.y-q.y)*(p.y-q.y)); }
int mini_fill(unsigned char *buf, unsigned long n) { for (unsigned long i = 0; i < n; i++) buf[i] = (unsigned char)(i * 2); return (int)n; }
int mini_parse(const char *s, int *out) { char *e; long v = strtol(s, &e, 10); if (*e) return 22; *out = (int)v; return 0; }
'''
fails = []
def chk(name, cond, extra=""):
    print(("ok    " if cond else "FAIL  ") + name + ("" if cond else "  -> " + extra))
    if not cond: fails.append(name)

d = tempfile.mkdtemp()
open(os.path.join(d, "mini.h"), "w").write(HEADER)
open(os.path.join(d, "mini.c"), "w").write(CODE)
r = subprocess.run(["gcc", "-shared", "-fPIC", "-o", os.path.join(d, "libmini.so"), os.path.join(d, "mini.c"), "-lm"], capture_output=True, text=True)
chk("C library compiles", r.returncode == 0, r.stderr)

def bg(*a):
    return subprocess.run([sys.executable, "-m", "moxie", "bindgen", *a], cwd=ROOT, capture_output=True, text=True)

r = bg(os.path.join(d, "mini.h"), "-o", os.path.join(d, "bindings.mxi"), "--lib", "mini")
text = open(os.path.join(d, "bindings.mxi")).read()
chk("generates declarations", r.returncode == 0 and "fn mini_add(a: Int32, b: Int32) Int32" in text, r.stderr)
chk("effects default to impure", "internal impure fn mini_add" in text)
chk("pointer and length fuse", "fn mini_sum(seed: UInt32, buf: Array[Byte], len: UInt = len(buf)) UInt32" in text)
chk("struct becomes a tuple", "internal tuple MiniPoint:" in text and "fn mini_dist(p: MiniPoint, q: MiniPoint) Double" in text)
chk("out-parameter becomes ref", "fn mini_parse(s: CString, ref out: Int32) Int32" in text)
chk("enum constants", "MINI_SAFE = 5" in text)
chk("header comment becomes ///", "/// Adds two numbers." in text)
chk("variadic and unpaired pointer are todos", all(f"todo: {n}" in text for n in ("mini_printf", "mini_bad")), text[-600:])
chk("opaque pointer becomes a handle", "  handle MiniCtx closes mini_close" in text and "fn mini_open(name: CString) Result[MiniCtx, Error]" in text and "fn mini_hits(c: MiniCtx) Int32" in text, text[-700:])

# sidecar: effects and pairing
open(os.path.join(d, "bindgen.toml"), "w").write('[functions.mini_add]\neffects = "pure"\n')
r = bg(os.path.join(d, "mini.h"), "-o", os.path.join(d, "bindings.mxi"), "--lib", "mini")
text = open(os.path.join(d, "bindings.mxi")).read()
chk("sidecar sets effects", "internal pure fn mini_add" in text)
chk("a writable buffer becomes ref Array[Byte]", "fn mini_fill(ref buf: Array[Byte], n: UInt = len(buf)) Int32" in text, text)

# end to end: wrappers over the generated bindings, called from moxie
prog = text + '''
export pure fn add(a: Int32, b: Int32) Int32: mini_add(a, b)
export fn parse_count(s: String) Result[Int32, Error]:
  n = 0i32
  code = mini_parse(cstr(s), ref n)
  if code ~= 0i32:
    return fail(22, "not a number")
  Ok(n)
println("${add(2i32, 3i32)} ${mini_sum(7u32, b"abc")} ${mini_dist(MiniPoint(0.0, 0.0), MiniPoint(3.0, 4.0))}")
println("${parse_count("42")} ${parse_count("x")}")
buf = b"\x00\x00\x00\x00"
k = mini_fill(ref buf)
println("$k $buf")
ctx = mini_open(cstr("A"))?
println("hits ${mini_hits(ctx)}")
mini_close(ctx)
'''
p = os.path.join(d, "main.mxi")
open(p, "w").write(prog)
r = subprocess.run([sys.executable, "-m", "moxie", "run", p], cwd=ROOT, capture_output=True, text=True)
exp_sum = (((7 * 31 + 97) * 31 + 98) * 31 + 99) & 0xFFFFFFFF
chk("end to end: calls the compiled library", r.returncode == 0 and f"5 {exp_sum} 5.0" in r.stdout and "Ok(42)" in r.stdout and "Err(" in r.stdout and "4 " in r.stdout and "hits 66" in r.stdout, r.stdout + r.stderr)

# --check drift
r = bg(os.path.join(d, "mini.h"), "-o", os.path.join(d, "bindings.mxi"), "--lib", "mini", "--check")
chk("--check finds no drift on a fresh file", r.returncode == 0 and "0 new, 0 removed, 0 changed" in r.stdout, r.stdout)
open(os.path.join(d, "mini.h"), "a").write("int mini_extra(int a);\n")
r = bg(os.path.join(d, "mini.h"), "-o", os.path.join(d, "bindings.mxi"), "--lib", "mini", "--check")
chk("--check reports a new function", r.returncode == 1 and "new: mini_extra" in r.stdout, r.stdout)

# --package
pk = os.path.join(d, "minipkg")
r = bg(os.path.join(d, "mini.h"), "--package", pk, "--lib", "mini")
chk("--package creates the layout", r.returncode == 0 and all(os.path.exists(os.path.join(pk, f)) for f in ("Moxie.toml", "bindings.mxi", "api.mxi")) and 'libs = ["mini"]' in open(os.path.join(pk, "Moxie.toml")).read(), r.stdout + r.stderr)

# a real system header
if os.path.exists("/usr/include/zlib.h"):
    r = bg("/usr/include/zlib.h", "-o", os.path.join(d, "zlib.mxi"), "--lib", "z")
    zt = open(os.path.join(d, "zlib.mxi")).read() if os.path.exists(os.path.join(d, "zlib.mxi")) else ""
    chk("zlib.h parses and declares crc32", r.returncode == 0 and re.search(r"fn crc32\(", zt) is not None, r.stdout + r.stderr)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
