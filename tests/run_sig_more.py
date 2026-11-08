"""Signatures for the I/O, UDP, timer, test-generator and misc prelude functions: wrong calls are compile errors, right calls pass."""
import sys, subprocess, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BAD = [
 ("println(show(1, 2))\n", "takes at most 1"),
 ("x = read_line(5)\n", "can't take"),
 ("x = read_bytes(stdin)\n", None),
 ("x = lines(\"f\")\n", "can't take"),
 ("x = port_of(3)\n", "can't take"),
 ("x = bind_udp(\"a\")\n", "can't take"),
 ("x = with_stdin(5, read_line)\n", "can't take"),
 ("x = remove_at(List(1, 2), \"a\")\n", "can't take"),
 ("assert_ne(1, \"a\")\n", "repeated type parameter"),
 ("t = after(1s)\narm(t, 5)\n", "can't take"),
 ("x = gen_int(seeded(1), 1, \"a\")\n", "repeated type parameter"),
 ("x = file_info(5)\n", "can't take"),
 ("x = connect_tls(\"h\")\nprintln(1)\n", None),
 ("x = listen_tls(1, \"c\", 3)\n", "can't take"),
 ("x = hash(1, 2)\n", "takes at most 1"),
 ("flush(1)\n", "can't take"),
 ("x = set(List(1, 2), 0, \"a\")\n", "repeated type parameter"),
 ("x = set(List(1, 2), \"i\", 3)\n", "can't take"),
 ("fn f(tx: ChanW[Int]) Unit:\n  write(tx, 1)\n", "mismatched types"),
 ("rx, tx = Chan[Int][1]()\n\\write(tx, \"a\")\n", "repeated type parameter"),
 ("fn feed(out: ChanW[String]) Unit:\n  \\write(out, 5)\n", "repeated type parameter"),
 ("fn drain(src: ChanR[Int]) Int:\n  read(src)?\nrx, tx = Chan[String]()\n\\drain(rx)\n", "expected `ChanR[Int]`"),
 ("a, b = (1, \"x\")\n\\write(a, 1)\n", "can't take"),
 ("r, w = Future[Int]()\nresolve(w, \"a\")\n", "repeated type parameter"),
 ("fn fin(x: FutureW[String]) Unit:\n  resolve(x, 1)\n", "repeated type parameter"),
 ("x = receive(5)\n", "can't take"),
 ("fn half(n: Int) Result[Int, String]:\n  Ok(n)\nx = traverse(half, 5)\n", "can't take"),
 ("x = guard(1)\n", "can't take"),
 ("x = sequence(List(1, 2))\n", "can't take"),
 ("fn f(e: Error) Int:\n  e.code\nprintln(f(5))\n", "expected `Error`"),
 ("e = Error(code: 1, message: \"m\")\nx: Int = e\n", "expected `Int`, found `Error`"),
 ("r, w = Future[Int]()\nreject(w, 5)\n", "can't take"),
 ("fn half(n: Int) Int:\n  n / 2\nx = traverse(half, List(1, 2))\n", "can't take"),
 ("fn half(n: Int) Int:\n  n / 2\nx = List(1, 2).filter(half) |> collect()\n", "can't take"),
 ("fn name_of(n: Int) String:\n  \"a\"\nfn apply(f: (Int) -> Int) Int:\n  f(1)\nprintln(apply(name_of))\n", "mismatched types"),
 ("fn two(a: Int, b: Int) Int:\n  a + b\nx = List(1, 2).map(two) |> collect()\n", "can't take"),
 ("enum Shape:\n  Circle(r: Int)\n  Sq(s: Int)\nx = traverse((n): Shape.Circle(n), List(1))\n", "can't take"),
 ("enum Shape:\n  Circle(r: Int)\n  Sq(s: Int)\nx = List(1).filter((n): Circle(n)) |> collect()\n", "can't take"),
 ("enum Shape:\n  Circle(r: Int)\n  Sq(s: Int)\nfn g() Bool:\n  Shape.Circle(1)\n", "expected `Bool`, found `Shape`"),
 ("enum Shape:\n  Circle(r: Int)\n  Sq(s: Int)\nc: Int = Shape.Circle(1)\n", "expected `Int`, found `Shape`"),
 ("enum Maybe[A]:\n  Just(value: A)\n  Nothing\nx = traverse((n): Just(n), List(1))\n", "can't take"),
 ("enum Maybe[A]:\n  Just(value: A)\n  Nothing\nz: Result[Int, String] = Maybe.Just(3)\n", "found `Maybe[?]`"),
 ("r1: Result[Int, String] = Ok(1)\nx = (r1, 5) |> map_all((a, b): a)\n", "can't take"),
 ("r1: Result[Int, String] = Ok(1)\nx = (r1, r1) |> map_all((a): a)\n", "takes 1 parameter"),
 ("r1: Result[Int, String] = Ok(1)\nr3: Result[Int, Int] = Ok(3)\nx = (r1, r3) |> map_all((a, b): a + b)\n", "can't take"),
 ("fn size(s: String) Int:\n  len(s)\nfn big(n: Int) Bool:\n  n > 1\nwords = List(\"a\", \"bb\")\nx = words.filter((s): s |> size) |> collect()\n", "can't take"),
 ("fn size(s: String) Int:\n  len(s)\nfn big(n: Int) Bool:\n  n > 1\nwords = List(\"a\", \"bb\")\nx = words.filter((s): s.size()) |> collect()\n", "can't take"),
 ("fn size(s: String) Int:\n  len(s)\nfn big(n: Int) Bool:\n  n > 1\nwords = List(\"a\", \"bb\")\nx = 5 |> size\n", "mismatched types"),
 ("fn apply(x: Int, f: (Int) -> Int) Int:\n  f(x)\nbad = (n: Int):\n  y = n + 1\n  \"s${y}\"\nr = apply(3, bad)\n", "mismatched types"),
 ("fn apply(x: Int, f: (Int) -> Int) Int:\n  f(x)\nfn on(f: (Int) -> Int, x: Int) Int:\n  f(x)\na = 3 |> on((x): \"s\")\n", "mismatched types"),
 ("fn apply(x: Int, f: (Int) -> Int) Int:\n  f(x)\nfn on(f: (Int) -> Int, x: Int) Int:\n  f(x)\nb = \"s\" |> apply((x): x)\n", "mismatched types"),
 ("fn apply(x: Int, f: (Int) -> Int) Int:\n  f(x)\nfn on(f: (Int) -> Int, x: Int) Int:\n  f(x)\nc = 3 |> apply(5)\n", "mismatched types"),
 ("fn apply(x: Int, f: (Int) -> Int) Int:\n  f(x)\nfn on(f: (Int) -> Int, x: Int) Int:\n  f(x)\nd = 3 |> apply()(x):\n  y = x + 1\n  \"t${y}\"\n", "mismatched types"),
 ("fn apply(x: Int, f: (Int) -> Int) Int:\n  f(x)\nfn on(f: (Int) -> Int, x: Int) Int:\n  f(x)\ne = 3 |> apply()(x): \"t${x}\"\n", "mismatched types"),
 ("fn both(a: Int, b: Int) Int:\n  a - b\nx = 3 |> both(10)\n", "is ambiguous"),
 ("x = fail(\"a\")\n", "can't take"),
 ("x = fail(1, 2)\n", "can't take"),
 ("x = fail(1, \"a\", 3)\n", "takes at most 2"),
]
GOOD = [
 "println(show(3))\nprintln(hash(\"a\"))\nflush()\nflush(stdout)\n",
 "x = remove_at(List(1, 2, 3), 1)\nprintln(x)\n",
 "r = with_stdin(\"hi\", read_line)\nprintln(r)\n",
 "r = read_line()\nr2 = read_all()\nprintln(stdin_lines() |> collect())\n",
 "assert_ne(1, 2)\ndebug_assert(true)\n",
 "t = after(1s)\narm(t, 5s)\n",
 "r = bind_udp(0)\nprintln(is_ok(r))\n",
 "fn f(x: Int) Result[Int, Error]:\n  if x > 1:\n    return fail(3, \"big\")\n  Ok(x)\nprintln(f(1))\n",
 "fn f(tx: ChanW[Int]) Unit:\n  \\write(tx, 1)\n",
 "rx, tx = Chan[Int][2]()\nt2 = clone(tx)\n\\write(tx, 1)\n\\write(t2, 2)\nprintln(read(rx)?)\n",
 "fn feed(out: ChanW[(Int, String)]) Unit:\n  \\write(out, (1, \"a\"))\nrx, tx = Chan[(Int, String)][1]()\nrun feed(tx)\nprintln(read(rx)?)\n",
 "fn pass[T](src: ChanR[T], out: ChanW[T]) Unit:\n  v = read(src)\n  when v:\n    Ok(x) -> \\write(out, x)\n    Err(_) -> ()\nprintln(1)\n",
 "a, b = (1, \"x\")\nprintln(a + len(b))\n",
 "r, w = Future[Int]()\nresolve(w, 42)\nwhen @r:\n  Pending -> println(\"waiting\")\n  Resolved(v) -> println(v)\n  Rejected(e) -> println(e.message)\n",
 "fn go() Result[Unit, Error]:\n  u = bind_udp(0)?\n  p = receive(u)?\n  println(p.host)\n  println(len(p.data))\n  Ok(())\nprintln(go())\n",
 "fn fin(x: FutureW[String]) Unit:\n  resolve(x, \"a\")\nfn rej(x: FutureW[Int]) Unit:\n  reject(x, Error(code: 1, message: \"m\"))\nprintln(1)\n",
 "fn half(n: Int) Result[Int, String]:\n  Ok(n)\nx = traverse(half, List(1, 2))\ny = sequence(List(Ok(1), Ok(2)))\nz = List(1, 2) |> to_stream() |> traverse(half)\nfn chk(n: Int) Result[Unit, Error]:\n  guard(n > 0)?\n  Ok(())\nprintln(x)\n",
 "fn f(e: Error) Int:\n  e.code\nfn g() Result[Int, Error]:\n  Err(Error(3, \"x\"))\nfn h() Result[Int, Error]:\n  fail(2, \"no\")\nfn j(r: Result[Int, Error]) String:\n  when r:\n    Ok(v) -> \"ok\"\n    Err(e) -> e.message\nprintln(f(Error(code: 1, message: \"m\")) + len(j(g())) + len(j(h())))\n",
 "fn double_in[F[_]: Monad](m: F[Int]) F[Int]:\n  m.flat_map((x): F.pure(x * 2))\nr: Result[Int, String] = Ok(21)\ns: Result[Int, Error] = Ok(21)\nprintln(double_in(r))\nprintln(double_in(s))\n",
 "fn half(n: Int) Int:\n  n / 2\nfn even(n: Int) Bool:\n  n % 2 == 0\nfn apply(f: (Int) -> Int) Int:\n  f(8)\nxs = List(1, 2).map(half) |> collect()\nys = List(1, 2).filter(even) |> collect()\nf = half\nprintln(apply(half) + f(4) + len(xs) + len(ys))\n",
 "fn pos(n: Int) Result[Int, String]:\n  if n > 0:\n    return Ok(n)\n  Err(\"neg\")\nprintln(traverse(pos, List(1, 2)))\nprintln(List(1, 2) |> to_stream() |> traverse(pos))\n",
 "fn reader() Int:\n  read_line().get_or(\"0\") |> len\nprintln(with_stdin(\"hi\", reader))\nfn flaky() Result[Int, String]:\n  Ok(1)\nprintln(retry(2, 1ms, flaky))\n",
 "enum Shape:\n  Circle(r: Int)\n  Sq(s: Int)\nfn area(s: Shape) Int:\n  when s:\n    Circle(r) -> r\n    Sq(n) -> n\nfn mk(n: Int) Shape:\n  Shape.Circle(n)\nfn pick(n: Int) Result[Shape, Shape]:\n  if n > 0:\n    return Ok(Shape.Sq(n))\n  Err(Shape.Circle(0))\nxs = List(Shape.Circle(1), Sq(2))\nu: Shape | () = Shape.Sq(1)\nprintln(area(mk(2)) + len(xs) + len(\"${pick(1)}\"))\nprintln(Shape.Circle(1) == Shape.Circle(1))\n",
 "enum Maybe[A]:\n  Just(value: A)\n  Nothing\nfn half(n: Int) Maybe[Int]:\n  if n % 2 == 0:\n    return Maybe.Just(n / 2)\n  Maybe.Nothing\nx: Maybe[Int] = Maybe.Just(3)\nprintln(\"${half(4)} ${x}\")\n",
 "fn add(a: Int, b: Int) Int:\n  a + b\nr1: Result[Int, String] = Ok(1)\nr2: Result[Int, String] = Ok(2)\nbad: Result[Int, String] = Err(\"no\")\nprintln(map_all(add, r1, r2))\nprintln((r1, r2) |> map_all(add))\nprintln((r1, r2).map_all(add))\nprintln((bad, r2, bad) |> map_all((a, b, c): a + b + c))\n",
 "fn size(s: String) Int:\n  len(s)\nfn big(n: Int) Bool:\n  n > 1\nwords = List(\"a\", \"bb\")\na = List(1, 2).filter((n): n |> big) |> collect()\nb = List(1, 2).filter((n): n.big()) |> collect()\nc = words.map((s): s |> size) |> collect()\nd = words.map((s): s.size()) |> collect()\nprintln(len(a) + len(b) + len(c) + len(d) + (\"abc\" |> size) + \"abc\".size())\n",
 "fn apply(x: Int, f: (Int) -> Int) Int:\n  f(x)\nok = (n: Int):\n  y = n + 1\n  y * 2\nearly = (n: Int):\n  if n > 5:\n    return 0\n  n\nprintln(apply(3, ok) + apply(9, early))\n",
 "fn apply(x: Int, f: (Int) -> Int) Int:\n  f(x)\nfn on(f: (Int) -> Int, x: Int) Int:\n  f(x)\nfn both(a: Int, b: Int) Int:\n  a - b\na = 3 |> apply()(x): x + 1\nb = 3 |> on()(x):\n  y = x * 2\n  y + 1\nc = 3 |> apply((x): x * 2)\nd = 3 |> on((x): x * 2)\nf = 10 |> both(&, 3)\ng = 3 |> both(10, &)\nprintln(a + b + c + d + f + g)\n",
 "xs = set(List(1, 2), 0, 5)\nd = set(Dict(1: 2), 3, 4)\nprintln(xs)\n",
 "rx, tx = Chan[Int][1]()\n\\write(tx, 1)\nprintln(read(rx))\n",
 "x = gen_int(seeded(1), 1, 5)\ny = gen_bool(seeded(1))\nz = gen_pick(seeded(1), List(1, 2))\nprintln(x)\n",
]
fails = 0
def chk(src, *flags):
    open("/tmp/_sigmore.mx", "w").write(src)
    return subprocess.run([sys.executable, "-m", "moxie", *flags, "check", "/tmp/_sigmore.mx"], capture_output=True, text=True)
for flags in ((), ("--gc",)):
    for src, msg in BAD:
        if msg is None:
            continue
        r = chk(src, *flags)
        if msg not in r.stdout + r.stderr:
            fails += 1; print("FAIL bad", flags, repr(src), r.stdout, r.stderr)
    for src in GOOD:
        r = chk(src, *flags)
        if r.returncode:
            fails += 1; print("FAIL good", flags, repr(src), r.stdout, r.stderr)
for flags in ((), ("--gc",)):
    r = chk("ys: Seq[Int] = List(1)\nfn f(x: Seq[Int]) Int:\n  1\n", *flags)
    n = (r.stdout + r.stderr).count("error:")
    if n != 2:                       # one `Seq` error per use, and no second "mismatched types" after it
        fails += 1; print("FAIL seq cascade", flags, n, r.stdout, r.stderr)
print("sig more: FAIL" if fails else "sig more: ok")
