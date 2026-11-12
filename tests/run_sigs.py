"""Prelude signatures (moxie/sigs.py): each sample is a declared type and an expression of that type.  The whole set must check and
run (so no signature gives a type the interpreter does not produce), and each sample with the wrong type must be an error
(so the signature is the one the checker uses).  Run: python3 tests/run_sigs.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PRE = 'xs = List(3, 1, 2)\nws = List("b", "a")\nd: Dict[String, Int] = Dict("a" -> 1)\nr: Result[Int, String] = Ok(4)\nat = Atom[Int](0)\n'
SAMPLES = [
 ("List[Int]", 'xs |> map((x) -> x + 1) |> collect()'),
 ("List[Int]", 'map((x) -> x + 1, xs)'),
 ("Stream[Int]", 'map((x) -> x + 1, to_stream(xs))'),
 ("Result[Int, String]", 'map((x) -> x + 1, r)'),
 ("List[Int]", 'xs |> filter((x) -> x > 1) |> collect()'),
 ("List[Int]", "xs |> take(2) |> collect()"),
 ("List[Int]", "xs |> drop(1) |> collect()"),
 ("List[Int]", 'xs |> take_while((x) -> x > 1) |> collect()'),
 ("List[Int]", 'xs |> drop_while((x) -> x > 1) |> collect()'),
 ("List[(Int, Int)]", "xs |> enumerate() |> collect()"),
 ("List[(Int, String)]", "zip(xs, ws) |> collect()"),
 ("List[Int]", "xs |> sort() |> collect()"),
 ("List[Int]", 'xs |> sort_by((x) -> 0 - x) |> collect()'),
 ("List[Int]", "xs |> reverse() |> collect()"),
 ("Int", 'xs |> reduce(0, (a, b) -> a + b)'),
 ("Int", "xs |> sum()"),
 ("Int", "xs |> product()"),
 ("Int", "xs |> count()"),
 ("Bool", 'xs |> any((x) -> x > 2)'),
 ("Bool", 'xs |> all((x) -> x > 2)'),
 ("Result[Int, Error]", 'xs |> find((x) -> x > 2)'),
 ("Result[Int, Error]", "xs |> first()"),
 ("Result[Int, Error]", "xs |> last()"),
 ("(List[Int], List[Int])", 'xs |> partition((x) -> x > 1)'),
 ("String", "upper(\"a\")"),
 ("Char", "upper('a')"),
 ("String", "lower(\"A\")"),
 ("Int", "abs(0 - 3)"),
 ("Double", "abs(0.0 - 2.5)"),
 ("Int", "min(1, 2)"),
 ("Int", "max(1, 2)"),
 ("Int", "clamp(5, 1, 3)"),
 ("Int", "pow(2, 3)"),
 ("Double", "pow(2.0, 3.0)"),
 ("Int", "floor(2.5)"),
 ("Int", "ceil(2.5)"),
 ("Int", "round(2.5)"),
 ("Double", "sqrt(4.0)"),
 ("Int", "len(\"abc\")"),
 ("String", "trim(\" a \")"),
 ("Bool", "starts_with(\"abc\", \"a\")"),
 ("Bool", "is_ok(r)"),
 ("List[Char]", "chars(\"ab\") |> collect()"),
 ("String", "pad_left(\"a\", 3)"),
 ("String", "pad_right(\"a\", 3, \"-\")"),
 ("List[String]", "split(\"a,b\", \",\")"),
 ("String", "join(ws, \",\")"),
 ("String", "replace_text(\"abc\", \"b\", \"x\")"),
 ("List[String]", "keys(d) |> collect()"),
 ("List[Int]", "values(d) |> collect()"),
 ("List[(String, Int)]", "items(d) |> collect()"),
 ("Result[Int, Error]", "get(d, \"a\")"),
 ("Result[Int, Error]", "get(xs, 0)"),
 ("Int", "get_or(r, 0)"),
 ("Int", "get_or(d, \"z\", 0)"),
 ("List[Int]", "xs |> distinct() |> collect()"),
 ("List[Int]", "List(xs, xs) |> flatten() |> collect()"),
 ("List[Int]", "xs |> intersperse(0) |> collect()"),
 ("List[Int]", 'zip_with((a, b) -> a + b, xs, xs) |> collect()'),
 ("Int", "identity(3)"),
 ("Result[Int, Error]", 'xs |> min_by((x) -> x)'),
 ("(List[Int], List[Int])", 'xs |> span((x) -> x > 2)'),
 ("(List[Int], List[Int])", "xs |> split_at(1)"),
 ("List[List[Int]]", "xs |> chunks(2) |> collect()"),
 ("Dict[Bool, List[Int]]", 'xs |> group_by((x) -> x > 1)'),
 ("Int", 'xs |> reduce_right(0, (a, b) -> a + b)'),
 ("List[Int]", 'xs |> scan(0, (a, b) -> a + b) |> collect()'),
 ("List[Int]", "xs |> take_last(2) |> collect()"),
 ("List[Int]", "xs |> to_stream() |> collect()"),
 ("Int", 'swap(at, (n) -> n + 1)'),
 ("Int", "reset(at, 5)"),
 ("Result[Int, Int]", 'map_err(r, (e) -> len(e))'),
 ("Result[String, String]", 'map_ok(r, (v) -> show(v))'),
 ("Int", "unwrap(r)"),
 ("Result[Unit, String]", "ensure(true, \"no\")"),
 ("String", "path_ext(\"a.txt\")"),
 ("String", "path_name(\"d/a.txt\")"),
 ("Int", "days_in_month(2024, 2)"),
 ("Unit", "assert(true)"),
 ("Bool", "contains(\"abc\", \"a\")"),
 ("Bool", "contains(xs, 1)"),
 ("Bool", "contains(d, \"a\")"),
 ("Double", "random()"),
 ("List[Int]", 'iterate(1, (n) -> n * 2) |> take(3) |> collect()'),
 ("Int", "random_int(1, 1)"),
 ("String", '"  hi ".trim()'),
 ("Bool", 'starts_with("abc", "a")'),
 ("Bool", 'starts_with("abc", \'a\')'),
 ("Bool", 'ends_with("abc", "c")'),
 ("Int", 'char_count("héllo")'),
 ("Int", 'grapheme_count("hello")'),
 ("String", 'path_join("a", "b")'),
 ("Bool", "is_ok(r)"),
 ("Bool", "is_err(r)"),
 ("Bool", "is_nan(1.5)"),
 ("Bool", "is_finite(1.5)"),
 ("Double", "sqrt(4.0)"),
 ("String", "cwd()"),
 ("List[Int]", 'xs |> distinct_by((x) -> x % 2) |> collect()'),
 ("List[(Int, String, Int)]", "zip3(xs, ws, xs) |> collect()"),
 ("Dict[Int, Int]", "frequencies(xs)"),
 ("Dict[Bool, Int]", 'count_by((x) -> x > 1, xs)'),
 ("List[List[Int]]", "transpose(List(xs, xs))"),
 ("(List[Int], List[String])", "partition_results(List(r, Err(\"x\")))"),
 ("Result[List[Int], List[String]]", "collect_errors(List(r, r))"),
 ("Result[List[Int], List[String]]", 'validate((x) -> Ok(x), xs) |> map_err((e) -> List("e"))'),
 ("Result[Int, String]", 'recover(r, (e) -> 0)'),
 ("Int", 'tap(3, (x) -> x)'),
 ("String", "os_name()"),
]
WRONG = {"Int": "String", "Double": "String", "Bool": "String", "String": "Int", "Char": "Int", "Unit": "Int"}


def run(cmd, src):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout.decode() + r.stderr.decode()


fails = []
src = PRE + "".join(f"v{i}: {t} = {e}\n" for i, (t, e) in enumerate(SAMPLES))
rc, o = run("run", src)
ok = rc == 0
print(("ok    " if ok else "FAIL  ") + f"{len(SAMPLES)} samples check and run" + ("" if ok else "\n" + o[:1500]))
if not ok:
    fails.append("samples")
for i, (t, e) in enumerate(SAMPLES):
    wrong = WRONG.get(t, "Bool" if t != "Bool" else "String")
    rc, o = run("check", PRE + f"v: {wrong} = {e}\n")
    bad = rc == 0 or "mismatched types" not in o
    if bad:
        print(f"FAIL  {e} is not seen as {t}: rc {rc} {o[:200]!r}")
        fails.append(e)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
