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
int mini_apply(int (*f)(int), int x);
int mini_connect(const char *name, mini_ctx **out);
void mini_make(int v, mini_ctx **out);
int mini_each(void (*f)(int, void *), void *user);
int mini_feed(const unsigned char *buf, unsigned long n, int (*f)(const unsigned char *, unsigned long, void *), void *ud);
int mini_walk(void (*f)(int *), int n);
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
int mini_apply(int (*f)(int), int x) { return f(x); }
int mini_each(void (*f)(int, void *), void *user) { for (int i = 1; i <= 3; i++) f(i, user); return 3; }
int mini_feed(const unsigned char *buf, unsigned long n, int (*f)(const unsigned char *, unsigned long, void *), void *ud) { return f(buf, n, ud); }
int mini_connect(const char *name, mini_ctx **out) { if (name[0] == 'x') { *out = NULL; return 5; } *out = malloc(sizeof **out); (*out)->hits = 100; return 0; }
void mini_make(int v, mini_ctx **out) { *out = malloc(sizeof **out); (*out)->hits = v; }
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
chk("function pointer becomes a function type", "fn mini_apply(f: (Int32) -> Int32, x: Int32) Int32" in text, text[-900:])
chk("callback with user data and a buffer", "fn mini_each(f: (Int32, UserData) -> Unit, user: UserData) Int32" in text and "fn mini_feed(buf: Array[Byte], n: UInt = len(buf), f: (Array[Byte], UInt, UserData) -> Int32, ud: UserData) Int32" in text, text[-900:])
chk("callback taking another pointer is a todo", "todo: mini_walk" in text, text[-500:])
chk("pointer to opaque pointer becomes an out-handle", "fn mini_connect(name: CString, ref out: MiniCtx) Result[MiniCtx, Error]" in text and "fn mini_make(v: Int32, ref out: MiniCtx) MiniCtx" in text, text[-1100:])
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
k = mini_connect(cstr("db"))?
println("connected ${mini_hits(k)}")
mini_close(k)
println(mini_connect(cstr("x")))
println("each ${mini_each(fn(v): println(\"item $v\")) }")
println("feed ${mini_feed(b\"abc\", fn(d): len(d))}")
println("apply ${mini_apply(fn(v): v * 7i32, 6i32)}")
ctx = mini_open(cstr("A"))?
println("hits ${mini_hits(ctx)}")
mini_close(ctx)
'''
p = os.path.join(d, "main.mxi")
open(p, "w").write(prog)
r = subprocess.run([sys.executable, "-m", "moxie", "run", p], cwd=ROOT, capture_output=True, text=True)
exp_sum = (((7 * 31 + 97) * 31 + 98) * 31 + 99) & 0xFFFFFFFF
chk("end to end: calls the compiled library", r.returncode == 0 and f"5 {exp_sum} 5.0" in r.stdout and "Ok(42)" in r.stdout and "Err(" in r.stdout and "4 " in r.stdout and "hits 66" in r.stdout and "apply 42" in r.stdout and "item 3" in r.stdout and "feed 3" in r.stdout and "connected 101" in r.stdout and "code: 5" in r.stdout, r.stdout + r.stderr)

# --wrap: default wrappers over the generated bindings
r = bg(os.path.join(d, "mini.h"), "-o", os.path.join(d, "bindings.mxi"), "--lib", "mini", "--wrap")
wtext = open(os.path.join(d, "wrappers.mxi")).read() if os.path.exists(os.path.join(d, "wrappers.mxi")) else ""
btext = open(os.path.join(d, "bindings.mxi")).read()
chk("--wrap strips the library prefix and converts text", "fn add(a: Int32, b: Int32) Int32: mini_add(a, b)" in wtext and "fn open_(name: String) Result[MiniCtx, Error]: mini_open(cstr(name))" in wtext, wtext[:900])
chk("--wrap turns status plus out-parameter into a Result", "fn parse(s: String) Result[Int32, Error]:" in wtext and "return fail(status," in wtext, wtext)
chk("--wrap hides user data in callback types", "fn each(f: (Int32) -> Unit) Int32: mini_each(f)" in wtext and "f: (Array[Byte]) -> Int32" in wtext, wtext)
chk("--wrap reports its guesses", "status:  mini_parse -> parse" in r.stdout, r.stdout)
prog2 = btext + wtext + '''
println("${add(2i32, 3i32)} ${parse("42")} ${parse("x")}")
c = connect_("db")?
println("hits ${hits(c)}")
close_(move c)
println("each ${each(fn(v): println("item $v"))}")
println("feed ${feed(b"abcd", fn(data): len(data))}")
'''
p2 = os.path.join(d, "wrapped.mxi")
open(p2, "w").write(prog2)
r2 = subprocess.run([sys.executable, "-m", "moxie", "run", p2], cwd=ROOT, capture_output=True, text=True)
chk("--wrap: the generated wrappers run", r2.returncode == 0 and "5 Ok(42) Err(Error(code: 22" in r2.stdout and "hits 101" in r2.stdout and "item 3" in r2.stdout and "feed 4" in r2.stdout, r2.stdout + r2.stderr)
# sidecar override
open(os.path.join(d, "bindgen.toml"), "w").write('[functions.mini_parse]\nreturns = "value"\n')
bg(os.path.join(d, "mini.h"), "-o", os.path.join(d, "bindings.mxi"), "--lib", "mini", "--wrap")
w2 = open(os.path.join(d, "wrappers.mxi")).read()
chk("returns = value keeps the raw shape", "fn parse(s: String, ref out: Int32) Int32: mini_parse(cstr(s), ref out)" in w2, w2)
os.remove(os.path.join(d, "bindgen.toml"))

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
