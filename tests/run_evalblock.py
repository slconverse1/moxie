"""`eval` blocks: `name <- e` desugars to flat_map.  Run: python3 tests/run_evalblock.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CASES = [
 ('Option: all steps succeed', 'fn half(n Int) Option[Int] = if n % 2 == 0 then Some(n / 2) else None\nr = eval\n  a <- half(20)\n  b <- half(a)\n  k = b + 1\n  Some(k * 2)\nprintln(r)\n', 0, 'Some(12)'),
 ('Option: a None stops the block', 'fn half(n Int) Option[Int] = if n % 2 == 0 then Some(n / 2) else None\nr = eval\n  a <- half(3)\n  b = a + 1\n  Some(b)\nprintln(r)\n', 0, 'None'),
 ('Result: an Err stops the block', 'fn parse(s String) Result[Int, String] = if s == "x" then Err("bad") else Ok(s.len())\nq = eval\n  a <- parse("abc")\n  b <- parse("x")\n  Ok(a + b)\nprintln(q)\n', 0, 'Err("bad")'),
 ('a bare line runs for its step', 'enum Cmd[A] deriving show\n  Say(text String) Cmd[Unit]\n  Ask Cmd[String]\nenum Prog[A] deriving show\n  Pure(a A)\n  Bind[X](cmd Cmd[X], k (X) -> Prog[A])\n\nfn say(t String) Prog[Unit] = Bind(Say(t), (u) -> Pure(()))\nfn ask() Prog[String] = Bind(Ask, (s) -> Pure(s))\n\nimpl Prog[A]\n  fn flat_map[B](self, f (A) -> Prog[B]) Prog[B] = when self\n    Pure(a) -> f(a)\n    Bind(c, k) -> Bind(c, (x) -> k(x).flat_map(f))\n\nfn exec[A](p Prog[A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Say(t) ->\n      println(t)\n      exec(k(()))\n    Ask -> exec(k("bob"))\n\nhello = eval\n  say("name?")\n  n <- ask()\n  say("hi ${n}")\nexec(hello)\n', 0, 'name?\nhi bob'),
 ('eval is a value: build, then run twice', 'enum Cmd[A] deriving show\n  Say(text String) Cmd[Unit]\n  Ask Cmd[String]\nenum Prog[A] deriving show\n  Pure(a A)\n  Bind[X](cmd Cmd[X], k (X) -> Prog[A])\n\nfn say(t String) Prog[Unit] = Bind(Say(t), (u) -> Pure(()))\nfn ask() Prog[String] = Bind(Ask, (s) -> Pure(s))\n\nimpl Prog[A]\n  fn flat_map[B](self, f (A) -> Prog[B]) Prog[B] = when self\n    Pure(a) -> f(a)\n    Bind(c, k) -> Bind(c, (x) -> k(x).flat_map(f))\n\nfn exec[A](p Prog[A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Say(t) ->\n      println(t)\n      exec(k(()))\n    Ask -> exec(k("bob"))\n\nhello = eval\n  n <- ask()\n  say("hi ${n}")\nexec(hello)\nexec(hello)\n', 0, 'hi bob\nhi bob'),
 ('State threads its state', '#gc\nimport fp.state\nfn next_id() state.State[Int, Int]\n  state.get().flat_map((n) -> state.put(n + 1).flat_map((u) -> state.get()))\np = eval\n  a <- next_id()\n  b <- next_id()\n  state.get().map((s) -> a + b + s)\nprintln(state.eval(p, 10))\n', 0, '35'),
 ('a block that ends in a binding is an error', 'x = eval\n  a <- Some(1)\n  b = 2\n', 2, 'ends with the value it gives'),
 ('a block that ends in a bind is an error', 'x = eval\n  a <- Some(1)\n  b <- Some(2)\n', 2, 'ends with the value it gives'),
 ('eval stays a legal name', 'eval = 3\nprintln(eval + 1)\nfn f(eval Int) Int = eval * 2\nprintln(f(4))\n', 0, '4\n8'),
 ('n < -x is still a comparison', 'n = -5\nx = 3\nprintln(n < -x)\n', 0, 'true'),
 ('an eval step on a user type without flat_map', 'tuple T() deriving show\nx = eval\n  a <- T()\n  Some(1)\n', 2, 'an `eval` step needs a value with a `flat_map` method, and `T` has none'),
 ('an eval step on a Bool', 'x = eval\n  a <- true\n  Some(a)\n', 2, '`Bool` has none'),
 ('an unknown method on a declared type is a check error', 'tuple T() deriving show\nprintln(T().nope(1))\n', 2, '`T` has no method `nope`'),
 ('a method, a field of function type and a free function still resolve', 'tuple T(f (Int) -> Int)\nimpl T\n  fn m(self) Int = 1\nfn free(t T) Int = 2\nt = T(f: (n) -> n + 1)\nprintln(t.m())\nprintln(t.f(1))\nprintln(t.free())\n', 0, '1\n2\n2'),
 ('fn eval and a call to it are ordinary', 'fn eval(n Int) Int = n + 1\nprintln(eval(2) + eval(3))\n', 0, '7'),
 ('a tuple pattern on the left of <-', 'fn pair(n Int) Option[(Int, Int)] = Some((n, n + 1))\nr = eval\n  (a, b) <- pair(1)\n  c <- Some(a + b)\n  Some(c * 10)\nprintln(r)\n', 0, 'Some(30)'),
 ('a tuple pattern still stops at None', 'fn pair(n Int) Option[(Int, Int)] = if n > 0 then Some((n, n)) else None\nr = eval\n  (a, b) <- pair(0)\n  Some(a + b)\nprintln(r)\n', 0, 'None'),
 ('eval impure allows a discarded print between steps', 'fn pair(n Int) Option[Int] = Some(n + 1)\nr = eval impure\n  a <- pair(1)\n  \\println("got ${a}")\n  b <- pair(a)\n  Some(a + b)\nprintln(r)\n', 0, 'got 2\nSome(5)'),
 ('eval pure is the explicit spelling of the default', 'fn pair(n Int) Option[Int] = Some(n + 1)\nr = eval pure\n  a <- pair(1)\n  b <- pair(a)\n  Some(a + b)\nprintln(r)\n', 0, 'Some(5)'),
 ('eval pure refuses a print and names eval impure', 'fn pair(n Int) Option[Int] = Some(n + 1)\nr = eval pure\n  a <- pair(1)\n  \\println("got ${a}")\n  Some(a)\n', 2, 'write `eval impure`'),
 ('a pure eval refuses a print and names eval impure', 'fn pair(n Int) Option[Int] = Some(n + 1)\nr = eval\n  a <- pair(1)\n  \\println("got ${a}")\n  Some(a)\n', 2, 'write `eval impure`'),
 ('the effect reaches the function that holds the block', 'fn pair(n Int) Option[Int] = Some(n + 1)\npure fn f() Option[Int] = eval impure\n  a <- pair(1)\n  \\println("x")\n  Some(a)\n', 2, 'pure'),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in ((True,) if src.startswith('#gc') else (False, True)):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = ((r.returncode != 0) if rc_want else r.returncode == 0) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
