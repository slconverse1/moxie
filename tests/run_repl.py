"""`moxie repl`: results, `it`, declarations, errors that leave the session alone, :type, :reset.  Run: python3 tests/run_repl.py"""
import subprocess, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (name, input, text that must appear in stdout, text that must appear in stderr or None, text that must not appear anywhere)
CASES = [
 ("an expression prints its type and value", "1 + 2\n", "$res1: Int = 3", None, None),
 ("$res1 is the latest result", "10\n$res1 * 2\n", "$res1: Int = 20", None, None),
 ("$res1 is the newest and older results move up", "5\n6\n$res1 + $res2\n", "$res1: Int = 11", None, None),
 ("older results keep their order", "5\n6\n7\n:results\n", "$res3: Int = 5", None, None),
 ("a binding prints its name and type", "x = 4.5\n", "x: Double = 4.5", None, None),
 ("a string result is quoted", '"abc"\n', '$res1: String = "abc"', None, None),
 ("a function stays for later inputs", 'fn sq(n Int) Int\n  n * n\n\nsq(9)\n', "$res1: Int = 81", None, None),
 ("a tuple type and its use", 'tuple P\n  a Int\n\np = P(a: 3)\np.a\n', "$res1: Int = 3", None, None),
 ("an error leaves the session as it was", "x = 1\nx + \"a\"\nx + 1\n", "$res1: Int = 2", "error:", None),
 ("a string's own $name is left alone", 'res1 = 7\n"n=$res1"\n', 'n=7', None, None),
 ("a user variable named res1 is not a result", "res1 = 7\n1 + 1\nres1\n", "$res1: Int = 7", None, None),
 ("a result that does not exist is an error", "$res5\n", "", "undefined name", None),
 ("an unknown name is an error", "nope\n", "", "undefined name", None),
 ("println output shows and is not bound", 'println("hi")\n1\n', "$res1: Int = 1", None, "res2"),
 ("side effects do not repeat", 'println("once")\n1\n2\n', "$res1: Int = 2", None, None),
 (":type shows a type without running", "x = 3\n:type x + 1\n", "Int", None, None),
 (":reset forgets everything", "x = 3\n:reset\nx\n", "session cleared", "undefined name", None),
 (":results lists them", "7\n8\n:results\n", "$res2: Int = 7", None, None),
 ("an abort ends only that input", "xs = List(1, 2)\nxs(5)\n3\n", "$res1: Int = 3", "abort", None),
 ("an unknown command", ":nope\n", "", "unknown command", None),
]
fails = []
for name, inp, out_has, err_has, absent in CASES:
    r = subprocess.run([sys.executable, "-m", "moxie", "repl"], input=inp, capture_output=True, text=True, cwd=ROOT, timeout=300)
    ok = out_has in r.stdout and (err_has is None or err_has in r.stderr) and (absent is None or absent not in r.stdout + r.stderr) and "Traceback" not in r.stderr
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> stdout {r.stdout.strip()[-200:]!r} stderr {r.stderr.strip()[-200:]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
