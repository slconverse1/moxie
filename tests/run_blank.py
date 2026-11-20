"""Blank lines are accepted everywhere: between arms, members, statements, arguments; a line of only white space (tabs too) is blank;
they are kept inside triple-quoted strings.  Run: python3 tests/run_blank.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CASES = {'when-arms': 'x = 2\nwhen x\n  1 -> println("a")\n\n  2 -> println("b")\n\n  _ -> println("c")\n', 'when-top-blank': 'x = 2\nwhen x\n\n  1 -> println("a")\n  _ -> println("c")\n', 'if-else': 'x = 2\nif x > 1\n  println("a")\n\nelse\n  println("b")\n', 'if-elif': 'x = 2\nif x > 5\n  println("a")\n\nelif x > 1\n  println("e")\n\nelse\n  println("b")\n', 'fn-body-blank-first': 'fn f(x Int) Int\n\n  x + 1\n\nprintln(f(1))\n', 'fn-blank-between': 'fn f(x Int) Int\n  y = x + 1\n\n  y * 2\n\nprintln(f(1))\n', 'list-lit': 'xs = List(\n  1,\n\n  2,\n\n  3\n)\nprintln(xs)\n', 'call-args': 'fn f(a Int, b Int) Int = a + b\nprintln(f(\n  1,\n\n  2\n))\n', 'params': 'fn f(\n  a Int,\n\n  b Int\n) Int = a + b\nprintln(f(1, 2))\n', 'tuple-decl': 'tuple P\n  a Int\n\n  b Int\n\nprintln(P(a: 1, b: 2))\n', 'tuple-decl-first': 'tuple P\n\n  a Int\n  b Int\nprintln(P(a: 1, b: 2))\n', 'enum-decl': 'enum C\n  R\n\n  G\n\n  B(n Int)\nprintln(C.R)\n', 'impl': 'tuple P\n  a Int\nimpl P\n  fn x(self) Int = self.a\n\n  fn y(self) Int = self.a + 1\nprintln(P(a: 1).y())\n', 'interface': 'interface S\n  fn a(self) Int\n\n  fn b(self) Int\ntuple Q\n  v Int\nimpl S for Q\n  fn a(self) Int = 1\n\n  fn b(self) Int = 2\nprintln(Q(v: 1).a())\n', 'for': 'for i in 1..3\n\n  println(i)\n\nprintln("d")\n', 'while': 'i = 0\nwhile i < 2\n\n  i += 1\n\nprintln(i)\n', 'pipe-cont': 'println(List(1,2,3)\n\n  |> map((x) -> x + 1)\n\n  |> collect())\n', 'dict-lit': 'd = Dict(\n  "a" -> 1,\n\n  "b" -> 2\n)\nprintln(d)\n', 'select': 'rx, tx = Chan[Int][1]()\n_ = write(tx, 1)\nselect\n\n  x = read(rx) -> println(x)\n\n  else\n    println(0)\n', 'update': 'tuple P\n  a Int\n  b Int\np = P(a: 1, b: 2)\nq = p.update\n  a: 5,\n\n  b: 6\nprintln(q)\n', 'blank-at-top': '\n\n\nprintln(1)\n', 'blank-at-end': 'println(1)\n\n\n\n', 'multi-clause-fn': 'fn f(0) Int = 1\n\nfn f(n Int) Int = n * f(n - 1)\n\nprintln(f(3))\n', 'guards': 'fn f(n Int) String\n  when n\n    x if x > 0 -> "p"\n\n    _ -> "n"\nprintln(f(1))\n', 'lambda-block': 'f = (x) ->\n\n  y = x + 1\n\n  y * 2\nprintln(f(1))\n', 'string-multiline': 's = """\n  a\n\n  b\n"""\nprintln(s)\n', 'daemon': 'daemon\n\n  println(1)\n  break daemon\n', 'match-nested': 'x = 2\nwhen x\n  1 ->\n    println("a")\n\n    println("a2")\n\n  _ ->\n    println("b")\n', 'let-else': 'o = Some(1)\nx = o else\n\n  println("no")\n  exit(1)\nprintln(x)\n', 'wait': 'wait s\n\n  println(1)\n\nprintln(2)\n', 'test': 'test "a"\n\n  assert_eq(1, 1)\n\n  assert_eq(2, 2)\n', 'ifexpr-cont': 'x = if true\n  1\n\nelse\n  2\nprintln(x)\n', 'comment-blank': 'x = 1\n\n// c\n\n/* b */\n\nprintln(x)\n', 'doc-comment': '/// doc\n\n/// more\nfn f() Int = 1\nprintln(f())\n', 'whitespace-only-lines': 'x = 1\n   \n\t\n \t \nprintln(x)\n', 'crlf-blank': 'x = 1\r\n\r\n\r\nprintln(x)\r\n'}


def run(src, cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False, newline="") as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    return r.returncode, (r.stdout + r.stderr).decode()


bad = 0
for name, src in CASES.items():
    rc, out = run(src, "check")
    print(("ok    " if rc == 0 else "FAIL  ") + name + ("" if rc == 0 else "  " + out.strip().splitlines()[-1][:100]))
    bad += rc != 0
rc, out = run('s = """\n  a\n\n  b\n"""\nprintln(s)\n')
ok = rc == 0 and out == "  a\n\n  b\n"
print(("ok    " if ok else "FAIL  ") + "triple-quoted keeps its blank lines")
bad += not ok
print(f"{bad} failed")
sys.exit(1 if bad else 0)
