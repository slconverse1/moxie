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
print("sig more: FAIL" if fails else "sig more: ok")
