"""UDP tests.  Run: python3 tests/run_udp.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ECHO = '''fn server(sock: Udp, done: ChanW[Int]) Unit:
  p = receive(sock, timeout: 3s)?
  _ = send_to(sock, p.host, p.port, p.data)
  _ = write(done, 1)

a = bind_udp(0)?
c = bind_udp(0)?
done_r, done_w = Chan[Int][1]()
_ = run server(a, done_w)
_ = send_to(c, "127.0.0.1", port_of(a), "ping")
r = receive(c, timeout: 3s)?
println("echo ${len(r.data)}")
'''

CASES = [
 ("a datagram arrives with its sender", 'a = bind_udp(0)?\nb = bind_udp(0)?\n_ = send_to(b, "127.0.0.1", port_of(a), "hello")\np = receive(a, timeout: 2s)?\nprintln("${p.host} ${len(p.data)} ${p.port == port_of(b)}")\n', ["--allow-all"], 0, "127.0.0.1 5 true"),
 ("bytes go as they are", 'a = bind_udp(0)?\nb = bind_udp(0)?\n_ = send_to(b, "127.0.0.1", port_of(a), b"\\x01\\x02\\x03")\np = receive(a, timeout: 2s)?\nprintln(p.data)\n', [], 0, "Array(1, 2, 3)"),
 ("port 0 picks a free port", 'a = bind_udp(0)?\nprintln(port_of(a) > 0)\n', [], 0, "true"),
 ("receive can time out", 'a = bind_udp(0)?\nprintln(receive(a, timeout: 100ms))\n', [], 0, "timed out"),
 ("a fiber waiting in receive does not stop the others", ECHO, [], 0, "echo 4"),
 ("an oversized datagram is an Err", 'a = bind_udp(0)?\nbig = "0123456789"\n' + 'big = big + big\n' * 13 + 'println(send_to(a, "127.0.0.1", 9, big))\n', [], 0, "at most 65507"),
 ("using a closed socket is a compile error", 'a = bind_udp(0)?\nclose(a)\nprintln(receive(a))\n', [], 2, "use of moved value `a`"),
 ("the address in use is an Err", 'a = bind_udp(0)?\nprintln(is_err(bind_udp(port_of(a))))\n', [], 0, "true"),
 ("bind_udp is checked against net.listen", 'println(bind_udp(7))\n', ["--allow-listen=8000-8010"], 0, "code: 10"),
 ("send_to is checked against net.connect", 'a = bind_udp(0)?\nprintln(send_to(a, "127.0.0.1", 9, "x"))\n', ["--allow-listen", "--allow-connect=example.com:53"], 0, "code: 10"),
 ("udp needs net (static)", 'println(bind_udp(0))\n', ["--allow-read"], 2, "needs net"),
 ("receive parks, so a pure fn may not call it", 'pure fn f(u: Udp) Int:\n  _ = receive(u)\n  1\n', [], 2, "pure fn 'f' parks"),
 ("a Udp is a resource that must be released", 'fn f() Unit:\n  a = bind_udp(0)?\n  b = a\n  close(a)\n  close(b)\n', [], 2, ""),
]
fails = []
for name, src, flags, rc_want, out_w in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, "run", f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    rc, o, e = r.returncode, r.stdout.decode(), r.stderr.decode()
    good = (rc == rc_want or (rc_want == 2 and rc != 0)) and out_w in (o + e)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} out={o!r} err={e[:160]!r}"))
    if not good: fails.append(name)

# the pool tally counts a UDP socket as an Io socket
with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
    f.write('a = bind_udp(0)?\nclose(a)\n')
r = subprocess.run([sys.executable, "-m", "moxie", "pools", f.name], cwd=ROOT, capture_output=True)
os.unlink(f.name)
o = (r.stdout + r.stderr).decode()
good = "Io socket" in o
print(("ok    " if good else "FAIL  ") + "the pool tally counts a Udp as an Io socket" + ("" if good else f"  -> {o!r}"))
if not good: fails.append("pools")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
