"""`dynamic fn`, `unsafe fn`, `safety = "strict"`, and `deriving dyn`.  Run: python3 tests/run_safety.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()

PERSON = '''import json
tuple Addr deriving dyn, show
  city String,
  zip Int
tuple Person deriving dyn, show
  name String,
  age Int,
  tags List[String],
  addr Addr,
  ok Bool
'''
MATH = 'foreign "m"\n  unsafe pure fn cos(x Double) Double\n  pure fn sin(x Double) Double\n'
MATHP = MATH + '  pure fn ptrsort(cmp (Ptr[Double], Ptr[Double]) -> Int32) Int32\n'
# (name, source, strict, rc_want, word in output)
CASES = [
 ("reading a Dyn in an untagged fn is an error", 'import json\nfn f(d json.Dyn) Result[Int, Error]\n  d.field("a")?.as_int()\n', False, 2, "must be declared `dynamic fn`"),
 ("dynamic fn may read a Dyn", 'import json\ndynamic fn f(d json.Dyn) Result[Int, Error]\n  d.field("a")?.as_int()\nprintln(f(json.parse("{\\"a\\": 4}")?))\n', False, 0, "Ok(4)"),
 ("top-level code may read a Dyn", 'import json\nd = json.parse("[7]")?\nprintln(d.at(0)?.as_int())\n', False, 0, "Ok(7)"),
 ("a lambda uses its enclosing fn's tag", 'import json\ndynamic fn f(d json.Dyn) Result[Int, Error]\n  d.as_list()?.map((x) -> x.as_int()) |> len() |> Ok\nprintln(f(json.parse("[1,2]")?))\n', False, 0, "Ok(2)"),
 ("a caller of a dynamic fn is fine by default", 'import json\ndynamic fn f(d json.Dyn) Result[Int, Error]\n  d.as_int()\nfn g(d json.Dyn) Result[Int, Error]\n  f(d)\nprintln(g(json.parse("5")?))\n', False, 0, "Ok(5)"),
 ("strict: a caller of a dynamic fn must be tagged", 'import json\ndynamic fn f(d json.Dyn) Result[Int, Error]\n  d.as_int()\nfn g(d json.Dyn) Result[Int, Error]\n  f(d)\n', True, 2, "with `safety = \"strict\"`"),
 ("strict: a tagged caller is fine", 'import json\ndynamic fn f(d json.Dyn) Result[Int, Error]\n  d.as_int()\ndynamic fn g(d json.Dyn) Result[Int, Error]\n  f(d)\nprintln(g(json.parse("5")?))\n', True, 0, "Ok(5)"),
 ("calling an unsafe foreign fn needs unsafe fn", MATH + 'fn f(x Double) Double\n  cos(x)\n', False, 2, "must be declared `unsafe fn`"),
 ("unsafe fn may call it", MATH + 'unsafe fn f(x Double) Double\n  cos(x)\nprintln(f(0.0))\n', False, 0, "1.0"),
 ("an undeclared foreign fn needs no tag", MATH + 'fn f(x Double) Double\n  sin(x)\nprintln(f(0.0))\n', False, 0, "0.0"),
 ("a foreign fn with a Ptr callback is unsafe", MATHP + 'fn f() Int32\n  ptrsort((a, b) -> 0i32)\n', False, 2, "must be declared `unsafe fn`"),
 ("strict: a caller of an unsafe fn must be tagged", MATH + 'unsafe fn f(x Double) Double\n  cos(x)\nfn g(x Double) Double\n  f(x)\n', True, 2, "it must be declared `unsafe fn` too"),
 ("a variable named dynamic is still a variable", 'dynamic = 3\nunsafe = dynamic + 1\nprintln(unsafe)\n', False, 0, "4"),
 ("deriving dyn round trip", PERSON + 'p = Person(name: "Al", age: 3, tags: List("a", "b"), addr: Addr(city: "X", zip: 5), ok: true)\nprintln(p.to_dyn().to_json())\ndynamic fn load(t String) Result[Person, Error]\n  Person.from_dyn(json.parse(t)?)\nprintln(load(p.to_dyn().to_json()) == Ok(p))\n', False, 0, "true"),
 ("from_dyn reports a wrong kind", PERSON + 'dynamic fn load(t String) Result[Person, Error]\n  Person.from_dyn(json.parse(t)?)\nprintln(load("{\\"name\\": 1}"))\n', False, 0, "not a String"),
 ("from_dyn reports a missing key", PERSON + 'dynamic fn load(t String) Result[Person, Error]\n  Person.from_dyn(json.parse(t)?)\nprintln(load("{\\"name\\": \\"a\\"}"))\n', False, 0, "no key"),
 ("from_dyn reports a bad list element", PERSON + 'dynamic fn load(t String) Result[Person, Error]\n  Person.from_dyn(json.parse(t)?)\nprintln(load("{\\"name\\": \\"a\\", \\"age\\": 1, \\"tags\\": [1]}"))\n', False, 0, "not a String"),
 ("from_dyn needs the tag", PERSON + 'fn load(t String) Result[Person, Error]\n  Person.from_dyn(json.parse(t)?)\n', False, 2, "must be declared `dynamic fn`"),
 ("a field with no Dyn form is refused", 'import json\ntuple T deriving dyn\n  f Dict[String, Int]\n', False, 2, "no `Dyn` form"),
 ("a generic tuple is refused", 'import json\ntuple T[A] deriving dyn\n  f A\n', False, 2, "generic"),
]
fails = []
for name, src, strict, rc_want, word in CASES:
    d = tempfile.mkdtemp(dir=D)
    open(os.path.join(d, "main.mxi"), "w").write(src)
    if strict:
        open(os.path.join(d, "Moxie.toml"), "w").write('[program]\nsafety = "strict"\n')
    r = subprocess.run([sys.executable, "-m", "moxie", "check" if rc_want == 2 else "run", "main.mxi"], cwd=d, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT, MOXIE_NATIVE_PATH=D))
    o = r.stdout + r.stderr
    good = (r.returncode != 0 if rc_want == 2 else r.returncode == 0) and word in o
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={r.returncode} {o.strip()[:300]}"))
    if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
