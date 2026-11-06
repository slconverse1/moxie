"""More prelude signatures: len (strings, collections, tuples), hash, time parsing, listen, spawn.  Run: python3 tests/run_sigs2.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAD = [
 ("len of a number", 'n = len(5)\n', "`len` can't take (Int)"),
 ("len gives an Int", 'n: String = len("x")\n', "expected `String`, found `Int`"),
 ("hash gives an Int", 'tuple P deriving eq, hash:\n  a: Int\nh: String = hash(P(a: 1))\n', "expected `String`, found `Int`"),
 ("parse_iso takes text", 'r = parse_iso(5)\n', "`parse_iso` can't take (Int)"),
 ("parse_time takes two strings", 'r = parse_time("2024", 3)\n', "`parse_time` can't take"),
 ("listen takes a port", 'l = listen("80")\n', "`listen` can't take (String)"),
 ("spawn takes a program name", 'c = spawn(1)\n', "`spawn` can't take (Int)"),
 ("accept takes a Listener", 'c = spawn("cat")?\nz = accept(c)\n', "`accept` can't take (Child)"),
 ("wait_child gives an Int", 'c = spawn("cat")?\nk: String = wait_child(c)\n', "expected `String`, found `Result[Int"),
 ("connect takes a port number", 'c = connect("localhost", "80")\n', "`connect` can't take (String, String)"),
 ("read_key takes a Terminal", 'k = read_key(5)\n', "`read_key` can't take (Int)"),
 ("run_command has no such option", 'r = run_command("echo", bogus: 1)\n', "`run_command` has no option `bogus`"),
 ("run_command option type", 'r = run_command("echo", cwd: 5)\n', "option `cwd` of `run_command` expects `String`, found `Int`"),
]
GOOD = [
 ("len of a tuple, collections and text", 'tuple P:\n  a: Int\n  b: Int\nprintln("${len("abc")} ${len(List(1, 2))} ${len(Dict("a": 1))} ${len((1, 2, 3))} ${len(P(a: 1, b: 2))}")\n', "3 2 1 3 2"),
 ("run_command with options", 'o = run_command("echo", List("hi"), stdin: "x", timeout: 5s)?\nprintln(o.stdout.trim())\nprintln(o.code)\n', "hi\n0"),
 ("spawn and wait_child", 'c = spawn("true")?\nprintln(wait_child(c)?)\nkill_child(c)\n', "0"),
 ("parse_iso and to_instant", 'd = parse_iso("2024-01-02")?\nprintln(iso(d))\n', "2024-01-02"),
]
fails = []


def run(cmd, src):
    f = os.path.join(tempfile.mkdtemp(), "main.mxi")
    open(f, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f], cwd=ROOT, capture_output=True, timeout=60)
    return r.returncode, r.stdout.decode() + r.stderr.decode()


for name, src, want in BAD:
    rc, o = run("check", src)
    ok = want in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name)
for name, src, want in GOOD:
    rc, o = run("run", src)
    ok = rc == 0 and want in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
