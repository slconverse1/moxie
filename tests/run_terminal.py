"""Raw terminal tests: raw_terminal, read_key, Key.  Run: python3 tests/run_terminal.py"""
import os, pty, select, subprocess, sys, tempfile, termios, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from moxie.terminal import _decode

fails = []
def check(name, ok, info=""):
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else "  " + str(info)[:300]))
    if not ok: fails.append(name)

def dec(data, wait=True):
    it = iter(data)
    buf = list(data)
    def get():
        return buf.pop(0) if buf else None
    return _decode(get, lambda: bool(buf) if wait else False)

DECODE = [
 (b"a", ("Typed", ["a"])), (b"\xc3\xa9", ("Typed", ["é"])), (b"\xe2\x82\xac", ("Typed", ["€"])),
 (b"\r", ("Enter", [])), (b"\n", ("Enter", [])), (b"\t", ("Tab", [])), (b"\x7f", ("Backspace", [])), (b"\x08", ("Backspace", [])),
 (b"\x03", ("Ctrl", ["c"])), (b"\x01", ("Ctrl", ["a"])), (b"\x00", ("Ctrl", [" "])),
 (b"\x1b[A", ("Up", [])), (b"\x1b[B", ("Down", [])), (b"\x1b[C", ("Right", [])), (b"\x1b[D", ("Left", [])),
 (b"\x1bOA", ("Up", [])), (b"\x1b[1;5C", ("Right", [])), (b"\x1b[H", ("Home", [])), (b"\x1b[F", ("End", [])),
 (b"\x1b[3~", ("Delete", [])), (b"\x1b[5~", ("PageUp", [])), (b"\x1b[6~", ("PageDown", [])), (b"\x1b[2~", ("Insert", [])),
 (b"\x1bOP", ("Fn", [1])), (b"\x1b[15~", ("Fn", [5])), (b"\x1b[24~", ("Fn", [12])),
 (b"\x1bx", ("Alt", ["x"])), (b"\x1b[99z", ("Other", [])),
]
for data, want in DECODE:
    check(f"decode {data!r}", dec(data) == want, dec(data))
check("a lone Escape is Escape", dec(b"\x1b", wait=False) == ("Escape", []))
check("end of input is None", dec(b"") is None)

PY = [sys.executable, "-m", "moxie"]
def run_pty(src, keys=(), flags=(), settle=0.3):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    m, s = pty.openpty()
    p = subprocess.Popen(PY + ["run", *flags, f.name], stdin=s, stdout=s, stderr=s, cwd=ROOT, close_fds=True)
    os.close(s)
    out = b""
    def drain(t):
        nonlocal out
        end = time.time() + t
        while time.time() < end:
            r, _, _ = select.select([m], [], [], 0.05)
            if r:
                try: d = os.read(m, 4096)
                except OSError: return
                if not d: return
                out += d
    drain(1.5)
    for k in keys:
        os.write(m, k); drain(settle)
    drain(0.6)
    try: p.wait(timeout=8)
    except Exception: p.kill(); p.wait()
    lflag = termios.tcgetattr(m)[3]
    os.unlink(f.name)
    os.close(m)
    return p.returncode, out.decode(errors="replace"), lflag

ECHO = termios.ECHO | termios.ICANON | termios.ISIG
LOOP = 'init:\n  t = raw_terminal()?\n  while:\n    k = read_key(t)?\n    when k:\n      Typed(c) -> println("typed $c")\n      Ctrl(c) -> println("ctrl $c")\n      Escape -> break\n      other -> println(other)\n  close(t)\n  println("bye")\n'

rc, out, lf = run_pty(LOOP, [b"a", b"\x03", b"\x1b[A", b"\x1b"])
check("keys arrive one at a time", rc == 0 and "typed a" in out and "ctrl c" in out and "Key.Up" in out and "bye" in out, (rc, out))
check("typed keys are not echoed", "a" not in out.replace("typed a", ""), out)
check("close puts the terminal back", rc == 0 and (lf & ECHO) == ECHO, lf)

ABORT = 'init:\n  t = raw_terminal()?\n  x = read_key(t)?\n  assert(false, "boom")\n'
rc, out, lf = run_pty(ABORT, [b"q"])
check("an abort still restores the terminal", rc != 0 and (lf & ECHO) == ECHO, (rc, lf, out))

OPEN = 'init:\n  t = raw_terminal()?\n  println("raw")\n'
rc, out, lf = run_pty(OPEN)
check("a Terminal left open is restored at exit", rc == 0 and "raw" in out and (lf & ECHO) == ECHO, (rc, lf))

TWICE = 'init:\n  a = raw_terminal()?\n  b = raw_terminal()?\n'
rc, out, lf = run_pty(TWICE)
check("a second Terminal is refused", rc != 0 and "already open" in out, out)

rc, out, lf = run_pty('init:\n  println(raw_terminal())\n', flags=["--platform=browser"])
check("the browser has no terminal key input", "not a terminal" in out or "MISSING" in out or "code: 4" in out, out)

def plain(src, flags=(), stdin=None):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run(PY + ["run", *flags, f.name], cwd=ROOT, capture_output=True, input=stdin or b"", timeout=60)
    os.unlink(f.name)
    return r.returncode, r.stdout.decode() + r.stderr.decode()

rc, out = plain('init:\n  println(raw_terminal())\n', stdin=b"")
check("piped input is not a terminal", rc == 0 and "not a terminal" in out and "code: 4" in out, (rc, out))
rc, out = plain('init:\n  println(raw_terminal())\n', flags=["--allow-read"])
check("raw_terminal needs stdin (static)", rc == 2 and "needs stdin" in out, (rc, out))
rc, out = plain('pure fn f() Int:\n  t = raw_terminal()\n  1\n', flags=["--allow-all"])
check("pure code cannot open a terminal", rc != 0 and "uses the system" in out, (rc, out))
rc, out, lf = run_pty('init:\n  t = raw_terminal()?\n  close(t)\n  println(read_key(t))\n')
check("reading a closed Terminal aborts", rc != 0 and "needs an open Terminal" in out and (lf & ECHO) == ECHO, (rc, out))

import re
_g = open(os.path.join(ROOT, "docs", "guide.md")).read()
_k = _g.index("**20h. Reading single keys**")
GUIDE = re.search(r"```\n(.*?)```", _g[_k:], re.S).group(1).replace("\\$", "$")
rc, out, lf = run_pty(GUIDE, [b"a", b"\x03", b"\x1b[A", b"\x1bOQ", b"\x1b"])
check("the guide example works", rc == 0 and "typed a" in out and "ctrl-c" in out and "up" in out and "F2" in out, (rc, out))

print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
