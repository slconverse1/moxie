"""The bottom-up reduce recipe from the Guide (chapter 14), in both dialects.  Run: python3 tests/run_memo.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []

FIB = '''fn fib(n: Int) Int:
  (a, _) = Range(1..=n, 1) |> reduce((0, 1), (s, _): (s(1), s(0) + s(1)))
  a
'''
GRID = '''fn next_row(prev: List[Int]) List[Int]:
  Range(1..len(prev), 1) |> reduce(List(prev(0)), (acc, j): acc + (prev(j) + acc(j - 1)))
fn paths(rows: Int, cols: Int) Int:
  first = List(1 for _ in 0..cols)
  last = Range(1..rows, 1) |> reduce(first, (prev, _): next_row(prev))
  last(cols - 1)
'''
LCS = '''fn step(prev: List[Int], acc: List[Int], ys: List[Char], x: Char, j: Int) Int:
  if ys(j - 1) == x:
    prev(j - 1) + 1
  else:
    max(prev(j), acc(j - 1))
fn lcs_row(prev: List[Int], x: Char, ys: List[Char]) List[Int]:
  Range(1..=len(ys), 1) |> reduce(List(0), (acc, j): acc + step(prev, acc, ys, x, j))
fn lcs(a: String, b: String) Int:
  xs = List(c for c in chars(a))
  ys = List(c for c in chars(b))
  last = xs |> to_stream() |> reduce(List(0 for _ in 0..=len(ys)), (prev, x): lcs_row(prev, x, ys))
  last(len(ys))
'''
CASES = [
 ("fib 10", FIB + 'println(fib(10))\n', "55"),
 ("fib 90 does not overflow Int", FIB + 'println(fib(90))\n', "2880067194370816120"),
 ("fib 0 is the base case", FIB + 'println(fib(0))\n', "0"),
 ("grid paths 3x3", GRID + 'println(paths(3, 3))\n', "6"),
 ("grid paths in one row", GRID + 'println(paths(1, 5))\n', "1"),
 ("grid paths 10x10", GRID + 'println(paths(10, 10))\n', "48620"),
 ("longest common subsequence", LCS + 'println(lcs("ABCBDAB", "BDCABA"))\n', "4"),
 ("lcs with an empty string", LCS + 'println(lcs("", "abc"))\n', "0"),
 ("lcs of kitten and sitting", LCS + 'println(lcs("kitten", "sitting"))\n', "4"),
]
for dialect in ([], ["--gc"]):
    for name, src, want in CASES:
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-m", "moxie", *dialect, "run", f.name], cwd=ROOT, capture_output=True, timeout=60)
        os.unlink(f.name)
        out = (r.stdout + r.stderr).decode()
        ok = r.returncode == 0 and out.strip() == want
        label = f"{name}{' (gc)' if dialect else ''}"
        print(("ok    " if ok else "FAIL  ") + label + ("" if ok else f"  (rc {r.returncode}) {out[:200]!r}"))
        if not ok: fails.append(label)
print()
print("FAILURES: " + ", ".join(fails) if fails else "all memoization tests passed")
sys.exit(1 if fails else 0)
