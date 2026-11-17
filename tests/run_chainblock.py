"""`chain` blocks: `name <- e` desugars to flat_map.  Run: python3 tests/run_chainblock.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CASES = [
 ('Option: all steps succeed', 'fn half(n Int) Option[Int] = if n % 2 == 0 then Some(n / 2) else None\nr = chain\n  a <- half(20)\n  b <- half(a)\n  k = b + 1\n  Some(k * 2)\nprintln(r)\n', 0, 'Some(12)'),
 ('Option: a None stops the chain', 'fn half(n Int) Option[Int] = if n % 2 == 0 then Some(n / 2) else None\nr = chain\n  a <- half(3)\n  b = a + 1\n  Some(b)\nprintln(r)\n', 0, 'None'),
 ('Result: an Err stops the chain', 'fn parse(s String) Result[Int, String] = if s == "x" then Err("bad") else Ok(s.len())\nq = chain\n  a <- parse("abc")\n  b <- parse("x")\n  Ok(a + b)\nprintln(q)\n', 0, 'Err("bad")'),
 ('a bare line runs for its step', 'enum Cmd[A]\n  Say(text String) Cmd[Unit]\n  Ask Cmd[String]\nenum Prog[A]\n  Pure(a A)\n  Bind[X](cmd Cmd[X], k (X) -> Prog[A])\n\nfn say(t String) Prog[Unit] = Bind(Say(t), (u) -> Pure(()))\nfn ask() Prog[String] = Bind(Ask, (s) -> Pure(s))\n\nimpl Prog[A]\n  fn flat_map[B](self, f (A) -> Prog[B]) Prog[B] = when self\n    Pure(a) -> f(a)\n    Bind(c, k) -> Bind(c, (x) -> k(x).flat_map(f))\n\nfn exec[A](p Prog[A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Say(t) ->\n      println(t)\n      exec(k(()))\n    Ask -> exec(k("bob"))\n\nhello = chain\n  say("name?")\n  n <- ask()\n  say("hi ${n}")\nexec(hello)\n', 0, 'name?\nhi bob'),
 ('chain is a value: build, then run twice', 'enum Cmd[A]\n  Say(text String) Cmd[Unit]\n  Ask Cmd[String]\nenum Prog[A]\n  Pure(a A)\n  Bind[X](cmd Cmd[X], k (X) -> Prog[A])\n\nfn say(t String) Prog[Unit] = Bind(Say(t), (u) -> Pure(()))\nfn ask() Prog[String] = Bind(Ask, (s) -> Pure(s))\n\nimpl Prog[A]\n  fn flat_map[B](self, f (A) -> Prog[B]) Prog[B] = when self\n    Pure(a) -> f(a)\n    Bind(c, k) -> Bind(c, (x) -> k(x).flat_map(f))\n\nfn exec[A](p Prog[A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Say(t) ->\n      println(t)\n      exec(k(()))\n    Ask -> exec(k("bob"))\n\nhello = chain\n  n <- ask()\n  say("hi ${n}")\nexec(hello)\nexec(hello)\n', 0, 'hi bob\nhi bob'),
 ('State threads its state', '#gc\nimport fp.state\nfn next_id() state.State[Int, Int]\n  state.get().flat_map((n) -> state.put(n + 1).flat_map((u) -> state.get()))\np = chain\n  a <- next_id()\n  b <- next_id()\n  state.get().map((s) -> a + b + s)\nprintln(state.eval(p, 10))\n', 0, '35'),
 ('a block that ends in a binding is an error', 'x = chain\n  a <- Some(1)\n  b = 2\n', 2, 'ends with the value it gives'),
 ('a block that ends in a bind is an error', 'x = chain\n  a <- Some(1)\n  b <- Some(2)\n', 2, 'ends with the value it gives'),
 ('chain stays a legal name', 'chain = 3\nprintln(chain + 1)\nfn f(chain Int) Int = chain * 2\nprintln(f(4))\n', 0, '4\n8'),
 ('n < -x is still a comparison', 'n = -5\nx = 3\nprintln(n < -x)\n', 0, 'true'),
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
