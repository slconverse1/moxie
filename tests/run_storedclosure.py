"""A capturing closure in a collection literal: an error in moxie, fine in moxie/gc; module-level names aren't captures.  Run: python3 tests/run_storedclosure.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = 'fn go(k Int) Unit\n  t Dict[String, (Int) -> Int] = Dict("a" -> (x Int) -> x * k)\n  println(t("a").unwrap()(5))\ngo(3)\n'
LST = 'fn go(k Int) Unit\n  t List[(Int) -> Int] = List((x Int) -> x + k)\n  println(len(t))\ngo(3)\n'
MOD = 'rate = 3\nt Dict[String, (Int) -> Int] = Dict("a" -> (x Int) -> x * rate)\nprintln(t("a").unwrap()(5))\n'
LOCALC = 'fn go(n Int) Unit\n  k = 3\n  m = k * 2\n  t Dict[String, (Int) -> Int] = Dict("a" -> (x Int) -> x * m)\n  println(t("a").unwrap()(5))\ngo(1)\n'
REBOUND = 'fn go(n Int) Unit\n  k = 3\n  k = k + n\n  t Dict[String, (Int) -> Int] = Dict("a" -> (x Int) -> x * k)\n  println(t("a").unwrap()(5))\ngo(1)\n'
PARAM = 'fn go(n Int) Unit\n  t Dict[String, (Int) -> Int] = Dict("a" -> (x Int) -> x * n)\n  println(t("a").unwrap()(5))\ngo(1)\n'
ENTRY_REBOUND = 'rate = 3\nrate += 1\nt Dict[String, (Int) -> Int] = Dict("a" -> (x Int) -> x * rate)\nprintln(t("a").unwrap()(5))\n'
LOOPED = 'fn go() Unit\n  k = 3\n  for i in List(1, 2)\n    k = k@1 + i\n  t Dict[String, (Int) -> Int] = Dict("a" -> (x Int) -> x * k)\n  println(t("a").unwrap()(5))\ngo()\n'
SAME = 'fn go(a Int, b Int) Unit\n  t = Dict("x" -> (v Int) -> v + a, "y" -> (v Int) -> v * b)\n  println(t("y").unwrap()(4))\ngo(2, 3)\n'
MIXED = 'fn go(a Int, s String) Unit\n  t = Dict("x" -> (v Int) -> v + a, "y" -> (v Int) -> len(s) + v)\n  println(t("x").unwrap()(1))\ngo(2, "ab")\n'
WRITTEN = 'fn go(a Int, b Int) Unit\n  t Dict[String, (Int) -> Int with (Int)] = Dict("x" -> (v Int) -> v + a, "y" -> (v Int) -> v * b)\n  println(t("y").unwrap()(4))\ngo(2, 3)\n'
WRITTEN_BAD = 'fn go(a Int, s String) Unit\n  t Dict[String, (Int) -> Int with (Int)] = Dict("x" -> (v Int) -> v + len(s))\ngo(2, "ab")\n'
NOWITH = 'fn go(a Int) Unit\n  t Dict[String, (Int) -> Int] = Dict("x" -> (v Int) -> v + a)\ngo(2)\n'
FIELD = 'tuple H\n  on (Int) -> Int with (Int)\nfn go(a Int) Unit\n  h = H(on: (v Int) -> v * a)\n  println(h.on(5))\ngo(2)\n'
FIELD_BAD = 'tuple H\n  on (Int) -> Int with (Int)\nfn go(s String) Unit\n  h = H(on: (v Int) -> v + len(s))\ngo("ab")\n'
ORDER = 'fn go(a Int, s String, b Int) Unit\n  t Dict[String, (Int) -> Int with (String, Int, Int)] = Dict("x" -> (v Int) -> v + a + b + len(s))\n  println(t("x").unwrap()(1))\ngo(2, "ab", 3)\n'
UPDATE_BAD = 'fn go(a Int, s String) Unit\n  t = Dict("x" -> (v Int) -> v + a)\n  t("y") = (v Int) -> v + len(s)\ngo(2, "ab")\n'
CASES = [
 ('closures with one capture layout share a Dict', SAME, False, 0, '12'),
 ('closures with different layouts cannot share a Dict', MIXED, False, 2, 'same kinds of values'),
 ('a written with-layout takes matching closures', WRITTEN, False, 0, '12'),
 ('a written with-layout refuses another layout', WRITTEN_BAD, False, 2, 'with (Int)'),
 ('a type written without with takes plain functions only', NOWITH, False, 2, 'write the type with a layout'),
 ('a tuple field of a with-type holds a matching closure', FIELD, False, 0, '10'),
 ('a tuple field of a with-type refuses another layout', FIELD_BAD, False, 2, 'with (Int)'),
 ('the order of the layout does not matter', ORDER, False, 0, '8'),
 ('an update with another layout is refused', UPDATE_BAD, False, 2, 'same kinds of values'),
 ('a local bound once to a constant is not a capture', LOCALC, False, 0, '30'),
 ('a local bound to a constant but rebound is a capture', REBOUND, False, 2, 'closure captures `k`'),
 ('a parameter is a capture', PARAM, False, 2, 'closure captures `n`'),
 ('an entry-file name that is rebound is a capture', ENTRY_REBOUND, False, 2, 'closure captures `rate`'),
 ('a name rebound in a loop is a capture', LOOPED, False, 2, 'closure captures `k`'),
 ('Dict literal captures a local', CAP, False, 2, 'only plain functions can be stored'),
 ('List literal captures a local', LST, False, 2, 'only plain functions can be stored'),
 ('moxie/gc stores it', CAP, True, 0, '15'),
 ('module-level name is not a capture', MOD, False, 0, '15'),
]
fails = []
for name, src, gc, rc_want, word in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    o = r.stdout + r.stderr
    ok = ((r.returncode == 0) == (rc_want == 0)) and word in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:200]}"))
    if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
