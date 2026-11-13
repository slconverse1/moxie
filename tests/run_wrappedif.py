"""A guard whose condition is wrapped onto its own indented line: `action` then `  if cond`, the same as `action if cond`.
Run: python3 tests/run_wrappedif.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
OK = [
 ("a call, condition true", 'n = 5\nprintln("big")\n  if n > 3\n', "big\n"),
 ("a call, condition false", 'n = 1\nprintln("big")\n  if n > 3\nprintln("end")\n', "end\n"),
 ("a long condition", 'n = 5\nq = false\nprintln("go")\n  if n > 3 and not q\n', "go\n"),
 ("same as the one-line form", 'n = 5\nprintln("a")\n  if n > 3\nprintln("a") if n > 3\n', "a\na\n"),
 ("return", 'fn f(n Int) Int\n  return 0\n    if n < 0\n  n\nprintln("${f(-3)} ${f(3)}")\n', "0 3\n"),
 ("continue and break in a loop", 'for i in 1..5 do\n  continue\n    if i == 2\n  break\n    if i == 4\n  println("i=$i")\n', "i=1\ni=3\n"),
 ("a return with fail", 'fn f(n Int) Result[Int, Error]\n  return fail(1, "negative")\n    if n < 0\n  Ok(n)\nprintln("${f(-1)} ${f(2)}")\n', 'Err(Error(code: 1, message: "negative")) Ok(2)\n'),
]
ERR = [
 ("a body under the if", 'n = 1\nprintln("x")\n  if n > 3\n    println("y")\n', "holds one `if cond` line"),
 ("an elif", 'n = 1\nprintln("x")\n  if n > 3\n  elif n > 1\n', "holds one `if cond` line"),
 ("an else", 'n = 1\nprintln("x")\n  if n > 3\n  else\n', "holds one `if cond` line"),
 ("a binding cannot be guarded", 'n = 1\nm = 5\n  if n > 3\n', "unexpected indent"),
 ("only an if may follow", 'n = 1\nprintln("x")\n  println("y")\n', "unexpected indent"),
]
fails = []
for name, src, want in OK:
    rc, out = run(src)
    good = rc == 0 and out == want
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:200]!r}"))
    if not good:
        fails.append(name)
for name, src, word in ERR:
    rc, out = run(src, "check")
    good = rc != 0 and word in out
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:200]!r}"))
    if not good:
        fails.append(name)
sys.exit(1 if fails else 0)
