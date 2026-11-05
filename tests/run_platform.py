"""Platform tests (Spec 19e): what Try moxie refuses at check time.  Run: python3 tests/run_platform.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CASES = [
 ("signals is refused in the browser", "check", 'rx = signals()\n', 1, "'signals' is not available in the browser"),
 ("signals is fine on a real system", None, 'rx = signals()\nprintln("ok")\n', 0, "ok"),
 ("a call reached through a function is refused too", "check", 'fn f() Unit:\n  _ = signals()\nf()\n', 1, "not available in the browser"),
 ("connect needs net, which the browser lacks", "check", 'println(connect("example.com", 80))\n', 1, "not granted (the browser)"),
 ("lookup_host needs net", "check", 'println(lookup_host("example.com"))\n', 1, "not granted (the browser)"),
 ("a listener needs net", "check", 'println(listen(8080))\n', 1, "not granted (the browser)"),
 ("udp needs net", "check", 'println(bind_udp(0))\n', 1, "not granted (the browser)"),
 ("files work (in memory in the page)", "run", 'write_file("a.txt", "hi")?\nprintln(read_file("a.txt")?)\nremove_file("a.txt")?\n', 0, "hi"),
 ("the clock and random work", "run", 'println(now().seconds() > 1.0)\nprintln(random_int(2, 2))\n', 0, "true\n2"),
 ("temp files work", "run", 'p = make_temp_file("t-")?\nprintln(path_exists(p))\nremove_file(p)?\n', 0, "true"),
 ("os_name says browser", "run", 'println(os_name())\n', 0, "browser"),
 ("is_terminal is false", "run", 'println(is_terminal(stdout))\n', 0, "false"),
 ("with_stdin still works", "run", 'println(with_stdin("hi\\n", read_line))\n', 0, "hi"),
]
fails = []
for name, cmd, src, rc_want, out_w in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    args = [sys.executable, "-m", "moxie"] + (["--platform=browser", cmd] if cmd else ["run"]) + [f.name]
    r = subprocess.run(args, cwd=tempfile.gettempdir() if cmd == "run" else ROOT, env={**os.environ, "PYTHONPATH": ROOT}, capture_output=True, timeout=60)
    os.unlink(f.name)
    rc, o = r.returncode, r.stdout.decode() + r.stderr.decode()
    ok = rc == rc_want and out_w in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {o[:300]!r}"))
    if not ok:
        fails.append(name)
r = subprocess.run([sys.executable, "-m", "moxie", "--platform=nope", "check", "x"], cwd=ROOT, capture_output=True)
ok = r.returncode == 2 and b"unknown platform" in r.stderr
print(("ok    " if ok else "FAIL  ") + "an unknown platform is refused")
if not ok:
    fails.append("unknown platform")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
