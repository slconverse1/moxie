"""`do with Enum:` blocks.  Run: python3 tests/run_with.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []

def run(src, args=()):
    d = tempfile.mkdtemp(prefix="mxopt")
    p = os.path.join(d, "t.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", *(args or ("run",)), p], cwd=ROOT, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr

def case(name, src, rc_want, want, args=()):
    rc, out = run(src, args)
    ok = rc == rc_want and want in out
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
    if not ok:
        fails.append(name)

case('do with opens the cases of an enum', 'enum Figure\n  Circle(r: Double)\n  Rect(w: Double, h: Double)\n  Dot\nenum Mode\n  Fast\n  Slow\ndo with Figure\n  println(Circle(r: 2.0))\n  println(Dot)\n', 0, 'Figure.Circle(2.0)\nFigure.Dot')
case('do with tells apart a case two enums share', 'enum Light\n  Red\n  Green\nenum Signal\n  Red\n  Stop\ndo with Light\n  println(Red)\ndo with Signal\n  println(Red)\n  println(Stop)\n', 0, 'Light.Red\nSignal.Red\nSignal.Stop')
case('do with opens several enums', 'enum Figure\n  Circle(r: Double)\n  Rect(w: Double, h: Double)\n  Dot\nenum Mode\n  Fast\n  Slow\nx = do with Figure, Mode\n  m = Fast\n  f = Circle(r: 1.0)\n  "${m} ${f}"\nprintln(x)\n', 0, 'Mode.Fast Figure.Circle(1.0)')
case('do with rewrites patterns', 'enum Figure\n  Circle(r: Double)\n  Rect(w: Double, h: Double)\n  Dot\nenum Mode\n  Fast\n  Slow\nfn d(f: Figure) String\n  do with Figure\n    when f\n      Circle(r) -> "circle ${r}"\n      Rect(_, _) -> "rect"\n      Dot -> "dot"\nprintln(d(Figure.Circle(r: 1.5)))\nprintln(d(Figure.Dot))\n', 0, 'circle 1.5\ndot')
case('do with can be inline and nested', 'enum A:\n  X\nenum B:\n  Z\ndo with A:\n  do with B:\n    println(X)\n    println(Z)\ndo with A: println(X)\n', 0, 'A.X\nB.Z\nA.X')
case('do with Option opens Some and None', 'do with Option\n  println(Some(3))\n  println(None)\n', 0, 'Some(3)\nNone')
case('a case two listed enums share is an error', 'enum Light\n  Red\n  Green\nenum Signal\n  Red\n  Stop\ndo with Light, Signal\n  println(Red)\n', 2, '`Red` is a case of both `Light` and `Signal`')
case('a case named like a function is an error', 'enum A\n  X\n  Y\nfn Y() Int = 1\ndo with A\n  println(1)\n', 2, 'also the name of a function or type')
case('do with naming no enum is an error', 'do with Nope\n  println(1)\n', 2, 'names no enum that is declared here')
case('with stays a plain name', 'with = 3\nprintln(with)\n', 0, '3')

case('a bare case two enums share is an error where nothing says which', 'enum Light\n  Red\n  Green\nenum Signal\n  Red\n  Stop\nprintln(Red)\n', 2, '`Red` could be `Light.Red` or `Signal.Red`')
case('a declared type says which enum a shared case means', 'enum Light\n  Red\n  Green\nenum Signal\n  Red\n  Stop\nx: Light = Red\nfn f() Signal\n  Red\nprintln(x)\nprintln(f())\n', 0, 'Light.Red\nSignal.Red')
case('a parameter, a field and a pattern say which enum', 'enum Light\n  Red\n  Green\nenum Signal\n  Red\n  Stop\nfn f(s: Signal) String\n  "${s}"\ntuple T\n  l: Light\nfn g(l: Light) String\n  when l\n    Red -> "r"\n    Green -> "g"\nprintln(f(Red))\nprintln(T(l: Red))\nprintln(g(Light.Red))\n', 0, 'Signal.Red\nT(l: Light.Red)\nr')
case("a program's own enum wins over the prelude's bare case", 'enum Dir\n  Up\n  Down\nprintln(Up)\n', 0, 'Dir.Up')
case("a program's own None wins over Option's unless a type says Option", 'enum Mode\n  None\n  Fast\nprintln(None)\nx: Option[Int] = None\nprintln(x)\n', 0, 'Mode.None\nNone')

case('a do with that uses a case has no warning', 'enum Light\n  Red\n  Green\nenum Mode\n  Fast\ndo with Light\n  println(Red)\n', 0, 'ok', args=('check',))
case('a do with that uses none of its cases is a warning', 'enum Light\n  Red\n  Green\nenum Mode\n  Fast\ndo with Light\n  println(1)\n', 0, 'this `do with Light:` block uses none of its cases', args=('check',))
case('a do with naming two enums warns about the unused one', 'enum Light\n  Red\n  Green\nenum Mode\n  Fast\ndo with Light, Mode\n  println(Red)\n', 0, '`do with Light, Mode:` never uses a case of `Mode`', args=('check',))

print(f"{len(fails)} failed" if fails else "all passed")
sys.exit(1 if fails else 0)
