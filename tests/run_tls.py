"""TLS connections (Spec 19c).  Run: python3 tests/run_tls.py   (needs the openssl command to make a test certificate)"""
import os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not shutil.which("openssl"):
    print("skipped: no openssl")
    sys.exit(0)
D = tempfile.mkdtemp()
subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", "key.pem", "-out", "cert.pem", "-days", "2",
                "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"], cwd=D, capture_output=True, check=True)
fails = []


def run(src, *flags, cmd="run"):
    p = os.path.join(D, "main.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, p], cwd=D, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT), timeout=60)
    return r.returncode, r.stdout + r.stderr


def chk(name, got, rc, *words):
    code, out = got
    good = code == rc and all(w in out for w in words)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={code} {out.strip()[:300]}"))
    if not good:
        fails.append(name)


SERVER = '''fiber fn server(tx ChanW[Int]) Result[Unit, Error]
  l = listen_tls(0, "cert.pem", "key.pem")?
  \\write(tx, port_of(l))
  c = accept(l)?
  println(c, "hello over tls")
  close(c)
  close(l)
  Ok(())
rx, tx = Chan[Int][1]()
run server(tx)
port = read(rx)?
'''
chk("a client that trusts the certificate talks to a TLS server", run(SERVER + 'c = connect_tls("localhost", port, ca: "cert.pem")?\nprintln(read_line(c)?)\nclose(c)\n'), 0, "hello over tls")
chk("an untrusted certificate is refused", run(SERVER.replace("c = accept(l)?", "c = accept(l)").replace("  println(c, ", "  println(") .replace("  close(c)\n  close(l)\n", "  close(l)\n") + 'r = connect_tls("localhost", port)\nprintln(r)\n'), 0, "certificate not trusted")
chk("connect_tls checks net.connect", run('println(connect_tls("127.0.0.1", 1))\n', "--allow-connect=example.com:443"), 0, "code: 10")
chk("a ca file needs fs.read", run('println(connect_tls("127.0.0.1", 1, ca: "cert.pem"))\n', "--allow-connect"), 0, "code: 10", "fs.read")
chk("listen_tls checks the key and certificate paths", run('println(listen_tls(0, "cert.pem", "key.pem"))\n', "--allow-listen"), 0, "code: 10", "fs.read")
chk("listen_tls with a bad file is an error value", run('println(listen_tls(0, "nope.pem", "nope.pem"))\n'), 0, "code: ")
chk("connect_tls without a net grant is a compile error", run('println(connect_tls("a", 1))\n', "--deny-all"), 2, "needs net.connect or net.listen")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
