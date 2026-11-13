"""The prelude `Option[T]` (Some / None).  Run: python3 tests/run_option.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []

def run(src):
    d = tempfile.mkdtemp(prefix="mxopt")
    p = os.path.join(d, "t.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", p], cwd=ROOT, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr

def case(name, src, rc_want, want):
    rc, out = run(src)
    ok = rc == rc_want and want in out
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
    if not ok:
        fails.append(name)

case('Some and None are bare and print bare', 'x Option[Int] = Some(2)\ny Option[Int] = None\nprintln(x)\nprintln(y)\nprintln(Some("a"))\n', 0, 'Some(2)\nNone\nSome("a")')
case('a when on an Option must cover both cases', 'fn f(o Option[Int]) Int\n  when o\n    Some(v) -> v\nprintln(f(Some(1)))\n', 2, '`when` does not cover `None`')
case('a when on an Option covered', 'fn f(o Option[Int]) String\n  when o\n    Some(v) -> "got ${v}"\n    None -> "nothing"\nprintln(f(Some(1)))\nprintln(f(None))\n', 0, 'got 1\nnothing')
case('? gives the value or returns None early', 'fn half(n Int) Option[Int]\n  if n % 2 == 0 then Some(n / 2) else None\nfn quarter(n Int) Option[Int]\n  h = half(n)?\n  half(h)\nprintln(quarter(8))\nprintln(quarter(6))\nprintln(quarter(3))\n', 0, 'Some(2)\nNone\nNone')
case('? on an Option in a function returning a Result is an error', 'fn h(n Int) Option[Int]\n  Some(n)\nfn g() Result[Int, Error]\n  x = h(1)?\n  Ok(x)\nprintln(g())\n', 2, '`?` on an `Option` returns `None` early')
case('? on a Result in a function returning an Option is an error', 'fn g() Option[Int]\n  x = read[Int]("5")?\n  Some(x)\nprintln(g())\n', 2, '`?` on a `Result` returns the error early')
case('? on a plain value says what it follows', 'fn g(n Int) Option[Int]\n  x = n?\n  Some(x)\nprintln(g(1))\n', 2, '`?` follows a `Result` or an `Option`')
case('? on None in an entry point ends the program', 'init\n  x = None\n  y = x?\n  println("no")\n', 1, 'error: `?` met `None`')
case('map, flat_map and |>> work on an Option', 'fn half(n Int) Option[Int]\n  if n % 2 == 0 then Some(n / 2) else None\nprintln(Some(3).map((x) -> x + 1))\nprintln(half(8).flat_map(half))\nprintln(half(8) |>> half |>> half)\nprintln(half(3) |>> half)\nprintln(Option.pure(5))\n', 0, 'Some(4)\nSome(2)\nSome(1)\nNone\nSome(5)')
case('is_some, is_none and get_or', 'println(is_some(Some(1)))\nprintln(is_none(Some(1)))\nprintln(get_or(None, 4))\nprintln(get_or(Some(2), 4))\nprintln(get_or(List(1, 2), 5, 9))\n', 0, 'true\nfalse\n4\n2\n9')
case('an Option compares and reads', 'println(Some(1) == Some(1))\nprintln(Some(1) ~= None)\nprintln(read[Option[Int]]("Some(7)"))\nprintln(read[Option[Int]]("None"))\nprintln(read[Option[Int]](show(Some(3))) == Ok(Some(3)))\n', 0, 'true\ntrue\nOk(Some(7))\nOk(None)\ntrue')
case('an Option sits in a list and a field', 'tuple P\n  nick Option[String]\nxs List[Option[Int]] = List(Some(1), None, Some(3))\nprintln(xs)\nprintln(P(nick: Some("z")))\nprintln(P(nick: None).nick)\n', 0, 'List(Some(1), None, Some(3))\nP(nick: Some("z"))\nNone')
case('a program may declare its own Option', 'enum Option\n  Yes\n  No\nprintln(Option.Yes)\n', 0, 'Option.Yes')
case('a program may use None as a case of its own enum', 'enum Mode\n  None\n  Fast\nm Mode = None\nprintln(m)\nwhen m\n  None -> println("n")\n  Fast -> println("f")\n', 0, 'Mode.None\nn')

print(f"{len(fails)} failed" if fails else "all passed")
sys.exit(1 if fails else 0)
