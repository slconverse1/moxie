"""Library helpers for functional code: distinct_by, zip3, frequencies, count_by, transpose, partition_results, collect_errors,
validate, recover, tap, retry.  Each program runs in both dialects with the same output.  Run: python3 tests/run_fplib.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ("distinct_by keeps the first per key", 'println(List(3, 1, 3, 2, 1) |> distinct_by((n) -> n % 2) |> collect())\n', "List(3, 2)"),
 ("zip3", 'println(zip3(List(1, 2), List("a", "b"), List(true, false)) |> collect())\n', 'List((1, "a", true), (2, "b", false))'),
 ("frequencies", 'println(frequencies(List("a", "b", "a")))\n', 'Dict("a" -> 2, "b" -> 1)'),
 ("count_by", 'println(count_by((n) -> n % 2 == 0, List(1, 2, 3, 4, 6)))\n', "Dict(false -> 2, true -> 3)"),
 ("transpose of ragged rows", 'println(transpose(List(List(1, 2, 3), List(4, 5), List(6))))\n', "List(List(1, 4, 6), List(2, 5), List(3))"),
 ("partition_results", 'println(partition_results(List(Ok(1), Err("x"), Ok(2))))\n', '(List(1, 2), List("x"))'),
 ("collect_errors gathers every error", 'println(collect_errors(List(Ok(1), Err("x"), Err("y"))))\n', 'Err(List("x", "y"))'),
 ("collect_errors all ok", 'println(collect_errors(List(Ok(1), Ok(2))))\n', "Ok(List(1, 2))"),
 ("validate gathers every error", 'fn check(n Int) Result[Int, String]\n  when n > 0\n    true -> Ok(n)\n    false -> Err("bad ${n}")\nprintln(validate(check, List(1, -2, 3, -4)))\n', 'Err(List("bad -2", "bad -4"))'),
 ("recover", 'println(recover(Err("e"), (e) -> 0))\nprintln(recover(Ok(5), (e) -> 0))\n', "Ok(0)\nOk(5)"),
 ("tap passes the value through", 'println(5.tap(fn (x) -> println("saw ${x}")))\n', "saw 5\n5"),
 ("retry calls again only after a failure", 'n = Atom[Int](0)\nfn flaky() Result[Int, String]\n  k = swap(n, _ + 1)\n  when k < 3\n    true -> Err("fail")\n    false -> Ok(k)\nprintln(retry(5, 1ms, flaky))\nprintln(@n)\n', "Ok(3)\n3"),
 ("retry gives the last Err", 'println(retry(2, 1ms, () -> Err("always")))\n', 'Err("always")'),
 ("retry does not repeat a permanent error", 'n = Atom[Int](0)\nfn gone() Result[Int, Error]\n  _ = swap(n, _ + 1)\n  Err(Error(NOT_FOUND, "gone"))\n_ = retry(4, 1ms, gone)\nprintln(@n)\n', "1"),
 ("retry repeats a transient error", 'n = Atom[Int](0)\nfn down() Result[Int, Error]\n  _ = swap(n, _ + 1)\n  Err(Error(IO_ERROR, "down"))\n_ = retry(3, 1ms, down)\nprintln(@n)\n', "3"),
 ("retry with when", 'n = Atom[Int](0)\nfn down() Result[Int, Error]\n  _ = swap(n, _ + 1)\n  Err(Error(IO_ERROR, "down"))\n_ = retry(3, 1ms, down, when: (e) -> false)\nprintln(@n)\n', "1"),
]
BAD = [
 ("distinct_by needs a function", 'xs = List(1)\nr = distinct_by(5, xs)\n', "`distinct_by` can't take"),
 ("retry has no such option", 'r = retry(2, 1ms, () -> Ok(1), nope: 1)\n', "`retry` has no option `nope`"),
]
fails = []


def run(cmd, src, gc=False):
    f = os.path.join(tempfile.mkdtemp(), "main.mxi")
    open(f, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + [cmd, f], cwd=ROOT, capture_output=True, timeout=60)
    return r.returncode, r.stdout.decode() + r.stderr.decode()


for name, src, want in CASES:
    a, b = run("run", src), run("run", src, True)
    ok = a[0] == 0 and a == b and a[1].strip() == want
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {a[1][:200]!r} / {b[1][:200]!r}"))
    if not ok:
        fails.append(name)
for name, src, want in BAD:
    rc, o = run("check", src)
    ok = rc != 0 and want in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
