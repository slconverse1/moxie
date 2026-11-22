"""fp.freer: the freer monad over a union of command enums, composable handlers, Has bounds on the command union.  Run: python3 tests/run_freer.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CASES = [
 ('a program over a union of command enums, one handler peeled off at a time', 'import fp.freer\nenum Say[A] deriving show\n  Print(text String) Say[Unit]\nenum Ask[A] deriving show\n  Name Ask[String]\nunion type Cmds[A] = Say[A] | Ask[A]\nunion type OnlyAsk[A] = Ask[A]\nfn handle_say[A](p freer.Prog[Cmds, A], acc List[String]) freer.Prog[OnlyAsk, (A, List[String])] = when p\n  Pure(a) -> freer.done((a, acc))\n  Bind(c, k) -> when c\n    Print(t) -> handle_say(k(()), acc + List(t))\n    Name -> freer.bind(Name, (x) -> handle_say(k(x), acc))\nfn run_ask[A](p freer.Prog[OnlyAsk, A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Name -> run_ask(k("bob"))\nhello freer.Prog[Cmds, Unit] = eval\n  n <- freer.send(Name)\n  freer.send(Print("hi ${n}"))\n(u, out) = run_ask(handle_say(hello, List()))\nprintln(out)\n', 0, 'List("hi bob")'),
 ('a command helper bound by Has builds in any union that holds the command', 'import fp.freer\nenum Say[A] deriving show\n  Print(text String) Say[Unit]\nenum Ask[A] deriving show\n  Name Ask[String]\nunion type Cmds[A] = Say[A] | Ask[A]\nunion type OnlyAsk[A] = Ask[A]\nfn say[C[_] Has[Say]](t String) freer.Prog[C, Unit] = freer.send(Print(t))\nx freer.Prog[Cmds, Unit] = say("hi")\n', 0, ''),
 ('a command helper bound by Has is refused for a union that lacks the command', 'import fp.freer\nenum Say[A] deriving show\n  Print(text String) Say[Unit]\nenum Ask[A] deriving show\n  Name Ask[String]\nunion type Cmds[A] = Say[A] | Ask[A]\nunion type OnlyAsk[A] = Ask[A]\nfn say[C[_] Has[Say]](t String) freer.Prog[C, Unit] = freer.send(Print(t))\nx freer.Prog[Cmds, Unit] = say("hi")\ny freer.Prog[OnlyAsk, Unit] = say("hi")\n', 2, '`OnlyAsk` has no `Say`, which `say` needs of `C`'),
 ('eval blocks over the freer monad', 'import fp.freer\nenum Say[A] deriving show\n  Print(text String) Say[Unit]\nenum Ask[A] deriving show\n  Name Ask[String]\nunion type Cmds[A] = Say[A] | Ask[A]\nfn run[A](p freer.Prog[Cmds, A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Print(t) ->\n      println(t)\n      run(k(()))\n    Name -> run(k("bob"))\nhello freer.Prog[Cmds, Unit] = eval\n  freer.send(Print("name?"))\n  n <- freer.send(Name)\n  freer.send(Print("hi ${n}"))\nrun(hello)\n', 0, 'name?\nhi bob'),
 ('map and the Monad interface work on programs', 'import fp.freer\nenum Say[A] deriving show\n  Print(text String) Say[Unit]\nenum Ask[A] deriving show\n  Name Ask[String]\nunion type Cmds[A] = Say[A] | Ask[A]\nfn run[A](p freer.Prog[Cmds, A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Print(t) -> run(k(()))\n    Name -> run(k("bob"))\nprintln(run(freer.send(Name).map((s) -> s.len())))\n', 0, '3'),
 ('a handler that misses a command is a compile error', 'import fp.freer\nenum Say[A] deriving show\n  Print(text String) Say[Unit]\nenum Ask[A] deriving show\n  Name Ask[String]\nunion type Cmds[A] = Say[A] | Ask[A]\nfn run[A](p freer.Prog[Cmds, A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Print(t) -> run(k(()))\n', 2, '`when` does not cover `Name`'),
 ('a handler with a catch-all arm is complete', 'import fp.freer\nenum Say[A] deriving show\n  Print(text String) Say[Unit]\nenum Ask[A] deriving show\n  Name Ask[String]\nunion type Cmds[A] = Say[A] | Ask[A]\nfn run[A](p freer.Prog[Cmds, A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Print(t) -> run(k(()))\n    _ -> run(k("x"))\nprintln(1)\n', 0, '1'),
 ('a handler for a one-command union needs only that command', 'import fp.freer\nenum Say[A] deriving show\n  Print(text String) Say[Unit]\nunion type One[A] = Say[A]\nfn run[A](p freer.Prog[One, A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Print(t) -> run(k(()))\nprintln(run(freer.done(3)))\n', 0, '3'),
 ('a locally written Prog is checked the same way', 'enum Say[A] deriving show\n  Print(text String) Say[Unit]\nenum Ask[A] deriving show\n  Name Ask[String]\nunion type Cmds[A] = Say[A] | Ask[A]\nenum Prog[C[_], A]\n  Pure(a A)\n  Bind[X](cmd C[X], k (X) -> Prog[C, A])\nfn run[A](p Prog[Cmds, A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Name -> run(k("bob"))\n', 2, '`when` does not cover `Print`'),
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
