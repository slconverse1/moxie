"""`tailrec fn` runs its tail calls as a loop (deep recursion is linear, not quadratic).  Run: python3 tests/run_tailrec.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CASES = [
 ('a tailrec count runs a hundred thousand steps', 'tailrec fn count(n Int, acc Int) Int = if n == 0 then acc else count(n - 1, acc + 1)\nprintln(count(100000, 0))\n', 0, '100000'),
 ('tail calls inside nested when and if', 'enum E\n  A(n Int)\n  B(n Int)\ntailrec fn go2(e E, acc Int) Int = when e\n  A(n) -> if n == 0 then acc else go2(B(n - 1), acc + 1)\n  B(n) -> when n\n    0 -> acc\n    _ -> go2(A(n - 1), acc + 1)\nprintln(go2(A(30000), 0))\n', 0, '30000'),
 ('a generic tailrec function with named arguments', 'tailrec fn rep[T](x T, n Int, acc Int) Int = if n == 0 then acc else rep(x: x, n: n - 1, acc: acc + 2)\nprintln(rep("a", 5000, 0))\n', 0, '10000'),
 ('a freer-monad handler as a tailrec function over 20000 commands', 'import fp.freer\nenum Say[A]\n  Print(text String) Say[Unit]\nunion type Cmds[A] = Say[A]\ntailrec fn run[A](p freer.Prog[Cmds, A]) A = when p\n  Pure(a) -> a\n  Bind(c, k) -> when c\n    Print(t) -> run(k(()))\nfn loop(n Int) freer.Prog[Cmds, Int] = if n == 0 then freer.done(7) else freer.send(Print("x")).flat_map((u) -> loop(n - 1))\nprintln(run(loop(20000)))\n', 0, '7'),
 ('a recursive call that is not in tail position is still an error', 'tailrec fn f(n Int) Int = if n == 0 then 0 else 1 + f(n - 1)\n', 2, 'not in tail position'),
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
