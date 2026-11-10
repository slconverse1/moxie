"""The `http` package: a client and a server talk over loopback, in both dialects; and a fiber abort ends the program
even while another fiber waits on a socket.  Run: python3 tests/run_http.py"""
import subprocess, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(ROOT, "tests")
EXPECT = "200 hello, mixer\n200 you said: héllo\n404 nothing at /nope\n"
fails = []

def run(name, args, ok):
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", *args], capture_output=True, text=True, cwd=ROOT, timeout=60)
        good = ok(r)
        detail = (r.stdout + r.stderr)[-300:]
    except subprocess.TimeoutExpired:
        good, detail = False, "timed out"
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> {detail!r}"))
    if not good:
        fails.append(name)

run("http loopback, moxie", ["run", os.path.join(T, "http_loopback.mxi")], lambda r: r.stdout == EXPECT)
run("http loopback, moxie/gc", ["--gc", "run", os.path.join(T, "http_loopback.mxi")], lambda r: r.stdout == EXPECT)
run("a fiber abort ends the program", ["run", os.path.join(T, "abort_with_open_socket.mxi")], lambda r: "abort in fiber server" in r.stderr and r.returncode != 0)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
