"""Units of measure: `unit m`, `5.0 m`, `Double[m/s]`; the checker rules for + - * / and comparison, the math built-ins.  Run: python3 tests/run_units.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, gc=False):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
U = "unit m\nunit s\nunit kg\nunit N = kg*m/s^2\n"
CASES = [
 ("a quantity prints as its number", U + "println(5.0 m)\n", "5.0"),
 ("an Int quantity", U + "println(3 m + 4 m)\n", "7"),
 ("units are erased at run time", U + "x = 2.5 m\nprintln(x * 2.0)\n", "5.0"),
 ("a function over quantities", U + "fn speed(d Double[m], t Double[s]) Double[m/s] = d / t\nprintln(speed(100.0 m, 4.0 s))\n", "25.0"),
 ("a derived unit equals its definition", U + "fn force(mass Double[kg], a Double[m/s^2]) Double[N] = mass * a\nf = force(2.0 kg, 9.8 m/s^2)\nw Double[kg*m/s^2] = f\nprintln(w)\n", "19.6"),
 ("a power in a literal", U + "a = 9.8 m/s^2\nprintln(a)\n", "9.8"),
 ("a power in a type", U + "fn area(w Int[m], h Int[m]) Int[m^2] = w * h\nprintln(area(3 m, 4 m))\n", "12"),
 ("parentheses in a type distribute", U + "fn sq(x Double[(m/s)^2]) Double[m^2/s^2] = x\nprintln(sq(4.0 m/s * 2.0 m/s))\n", "8.0"),
 ("a ratio of equal units is a plain number", U + "r = 10.0 m / 2.0 m\nz Double = r\nprintln(z)\n", "5.0"),
 ("a quantity times a plain number", U + "d = 3.0 m\nprintln(d * 2.0)\nprintln(2 * d)\nprintln(d / 2)\n", "6.0\n6.0\n1.5"),
 ("negation keeps the unit", U + "d Double[m] = -(3.0 m)\nprintln(d)\n", "-3.0"),
 ("comparison of like units", U + "println(3.0 m < 5.0 m)\n", "true"),
 ("sum and max of quantities", U + "xs = List(1.0 m, 2.0 m, 3.0 m)\nprintln(sum(xs))\nprintln(max(1.0 m, 2.0 m))\n", "6.0\n2.0"),
 ("abs keeps the unit", U + "d Double[m] = abs(-3.0 m)\nprintln(d)\n", "3.0"),
 ("sqrt halves the unit", U + "d Double[m] = sqrt(4.0 m^2)\nprintln(d)\n", "2.0"),
 ("pow multiplies the unit", U + "a Double[m^2] = pow(3.0 m, 2)\nprintln(a)\n", "9.0"),
 ("floor keeps the unit on an Int", U + "n Int[m] = floor(2.5 m)\nprintln(n)\n", "2"),
 ("magnitude drops the unit", U + "d Double = magnitude(3.0 m)\nprintln(d)\n", "3.0"),
 ("a plain number is attached with a literal", U + "x = 4.0\nd Double[m] = x * 1.0 m\nprintln(d)\n", "4.0"),
 ("adding different units", U + "bad = 1.0 m + 2.0 s\n", "cannot add `Double[m]` and `Double[s]`: the units differ (m and s)"),
 ("adding a plain number", U + "bad = 1.0 m + 2.0\n", "give a plain number its unit first, such as `2.0 m`"),
 ("subtracting different units", U + "bad = 1.0 m - 2.0 kg\n", "cannot subtract"),
 ("comparing different units", U + "bad = 1.0 m < 2.0 s\n", "cannot compare `Double[m]` and `Double[s]`"),
 ("an argument in the wrong unit", U + "fn f(d Double[m]) Double[m] = d\nbad = f(1.0 s)\n", "expected `Double[m]`, found `Double[s]`"),
 ("a plain number where a quantity is expected", U + "bad Double[m] = 3.0\n", "expected `Double[m]`, found `Double`"),
 ("a quantity where a plain number is expected", U + "bad Double = 3.0 m\n", "expected `Double`, found `Double[m]`"),
 ("a wrong return unit", U + "fn f(d Double[m], t Double[s]) Double[m] = d / t\n", "Double[m]"),
 ("sqrt of an odd power", U + "bad = sqrt(4.0 m)\n", "`sqrt` of `Double[m]` has no whole unit"),
 ("product of quantities", U + "bad = product(List(1.0 m, 2.0 m))\n", "`product` of `Double[m]` values has no single unit"),
 ("pow with a variable exponent", U + "n = 2\nbad = pow(2.0 m, n)\n", "must be a constant whole number"),
 ("an undeclared unit in a literal stays an ordinary expression", "x = 5\nprintln(x)\n", "5"),
 ("an undeclared unit in a type", "fn f(x Double[meter]) Double = 1.0\nprintln(1)\n", "`meter` is not a unit"),
 ("a variable called unit still works", "enum Shape\n  Circle(radius Double),\n  Empty\nunit Shape = Circle(radius: 1.0)\nprintln(unit)\n", "Circle(1.0)"),
 ("a unit declared twice", "unit m\nunit m\n", "the unit `m` is declared twice"),
 ("a derived unit from an undeclared unit", "unit N = kg*m\n", "`kg` is not a unit"),
 ("a duration literal is still a Duration", U + "println(5s)\n", "5s"),
 ("an Int quantity divides as an Int", U + "x Int[m/s] = 7 m / 2 s\nprintln(x)\n", "3"),
]
fails = []
for name, src, want in CASES:
    for gc in (False, True):
        rc, out = run(src, gc)
        good = want in out
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
        if not good:
            fails.append(name)
print(f"{len(CASES) * 2 - len(fails)} of {len(CASES) * 2} passed")
sys.exit(1 if fails else 0)
