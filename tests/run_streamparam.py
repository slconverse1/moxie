"""A parameter declared `Stream[T]` accepts any collection of T as it stands.  Run: python3 tests/run_streamparam.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = "fn evens(xs Stream[Int]) List[Int]\n  xs |> filter(_ % 2 == 0) |> collect()\n"
OK = [("println(evens(List(1, 2, 3, 4)))", "List(2, 4)"), ("println(evens(Set(2, 3)))", "List(2)"), ("println(evens(Array(4, 5, 6)))", "List(4, 6)"),
      ("println(evens(1..6))", "List(2, 4, 6)"), ("println(evens(Some(4)))", "List(4)"),
      ("println(evens(List(1, 2, 3) |> map(_ + 1)))", "List(2, 4)"),
      ('fn keys_of(xs Stream[(String, Int)]) List[String]\n  xs |> map((k, v) -> k) |> collect()\nprintln(keys_of(Dict("a" -> 1)))', 'List("a")'),
      ('fn shout(xs Stream[Char]) List[Char]\n  xs |> map(upper(_)) |> collect()\nprintln(shout("hi"))', 'List("H", "I")'),
      ('fn firsts[T](xs Stream[T]) List[T]\n  xs |> take(2) |> collect()\nprintln(firsts(List("a", "b", "c")))', 'List("a", "b")')]
BAD = [('println(evens(List("a")))', "mismatched types"), ('println(evens("abc"))', "mismatched types"), ('println(evens(Set("x")))', "mismatched types")]
bad = 0
def run(src, gc):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f: f.write(HEAD + src + "\n")
    r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name); return r
for gc in (False, True):
    for src, want in OK:
        r = run(src, gc); ok = r.returncode == 0 and r.stdout.strip() == want
        print(("ok    " if ok else "FAIL  ") + ("gc " if gc else "") + src.splitlines()[-1][:60] + ("" if ok else " -> " + (r.stdout + r.stderr)[-100:])); bad += not ok
    for src, want in BAD:
        r = run(src, gc); ok = r.returncode != 0 and want in r.stderr + r.stdout
        print(("ok    " if ok else "FAIL  ") + ("gc " if gc else "") + "rejects " + src[:50]); bad += not ok
sys.exit(1 if bad else 0)
