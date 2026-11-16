"""GADTs: a case states its own result type; `when` arms learn the type parameter.  Run: python3 tests/run_gadt.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
VAL = """enum Value[T]
  Num(n Int) Value[Int]
  Flag(b Bool) Value[Bool]
  Add(a Value[Int], b Value[Int]) Value[Int]
  Eq(a Value[Int], b Value[Int]) Value[Bool]
  If(c Value[Bool], t Value[T], e Value[T])
"""
EVAL = """fn eval[T](v Value[T]) T = when v
  Num(n) -> n
  Flag(b) -> b
  Add(a, b) -> eval(a) + eval(b)
  Eq(a, b) -> eval(a) == eval(b)
  If(c, t, e) -> if eval(c) then eval(t) else eval(e)
"""
CASES = [
 ("a typed evaluator runs", VAL + EVAL + "println(eval(Add(Num(1), Num(2))))\nprintln(eval(If(Eq(Num(1), Num(1)), Num(5), Num(6))))\nprintln(eval(Eq(Num(2), Num(3))))\n", 0, "3\n5\nfalse"),
 ("adding a Bool is an error", VAL + "x = Add(Num(1), Flag(true))\n", 2, "expected `Value[Int]`, found `Value[Bool]`"),
 ("an arm returning the wrong type", VAL + "fn bad[T](v Value[T]) T = when v\n  Num(n) -> true\n  Flag(b) -> b\n  Add(a, b) -> 0\n  Eq(a, b) -> false\n  If(c, t, e) -> t\n", 2, "expected `Int`, found `Bool`"),
 ("a result type that does not match the call", VAL + EVAL + "fn f() Bool = eval(Num(1))\n", 2, "expected `Bool`, found `Int`"),
 ("a concrete value needs only its possible cases", VAL + "fn f(v Value[Int]) Int = when v\n  Num(n) -> n\n  Add(a, b) -> f(a) + f(b)\n  If(c, t, e) -> 0\n", 0, ""),
 ("an impossible case is an error", VAL + "fn f(v Value[Bool]) Bool = when v\n  Num(n) -> true\n  Flag(b) -> b\n  Eq(a, b) -> true\n  If(c, t, e) -> true\n", 2, "can never match"),
 ("a missing possible case is an error", VAL + "fn f(v Value[Int]) Int = when v\n  Num(n) -> n\n", 2, "does not cover"),
 ("a generic value needs every case", VAL + "fn f[T](v Value[T]) Int = when v\n  Num(n) -> n\n", 2, "does not cover"),
]

EX = """enum Value[T]
  Num(n Int) Value[Int]
  Flag(b Bool) Value[Bool]
  Pair(a Value[A], b Value[B]) Value[(A, B)]
  Fst(p Value[(A, B)]) Value[A]
  Same(a Value[A], b Value[A]) Value[Bool]
  Packed(v Value[A], f (A) -> String) Value[String]
"""
EXEVAL = """fn eval[T](v Value[T]) T = when v
  Num(n) -> n
  Flag(b) -> b
  Pair(a, b) -> (eval(a), eval(b))
  Fst(p) -> eval(p)(0)
  Same(a, b) -> eval(a) == eval(b)
  Packed(v, f) -> f(eval(v))
"""
CASES += [
 ("a case variable in the result type", EX + EXEVAL + "println(eval(Pair(Num(1), Flag(true))))\nprintln(eval(Fst(Pair(Num(7), Flag(false)))))\n", 0, "(1, true)\n7"),
 ("a variable only in the payloads (existential)", EX + EXEVAL + 'println(eval(Packed(Num(41), (n) -> "n=${n + 1}")))\nprintln(eval(Packed(Flag(true), (b) -> if b then "yes" else "no")))\n', 0, "n=42\nyes"),
 ("a variable bound twice must agree", EX + "x = Same(Num(1), Flag(true))\n", 2, "expected `Value[Int]`, found `Value[Bool]`"),
 ("a function over the wrong variable", EX + 'fn isb(b Bool) String = "x"\nx = Packed(Num(1), isb)\n', 2, "expected `(Int) -> String`, found `(Bool) -> String`"),
 ("the pair type is inferred", EX + "fn f() Value[Int] = Pair(Num(1), Num(2))\n", 2, "found `Value[(Int, Int)]`"),
 ("a payload that is not a Value", EX + "x = Pair(Num(1), 5)\n", 2, "found `Int`"),
 ("an arm that returns one half of the pair", EX + "fn bad[T](v Value[T]) T = when v\n  Num(n) -> n\n  Flag(b) -> b\n  Pair(a, b) -> eval(a)\n  Fst(p) -> eval(p)(0)\n  Same(a, b) -> true\n  Packed(v, f) -> f(eval(v))\n" + EXEVAL.replace("fn eval", "fn eval"), 2, "expected `(A', B')`, found `A'`"),
]
CASES += [
 ("an untyped lambda gets its parameter type from the case", EX + 'x = Packed(Num(1), (b) -> if b then "y" else "n")\n', 2, "`if` condition must be `Bool`, found `Int`"),
 ("a typed lambda over the wrong type", EX + 'x = Packed(Num(1), (b Bool) -> "x")\n', 2, "found a function taking `Bool`"),
 ("an untyped lambda that fits", EX + EXEVAL + 'println(eval(Packed(Num(1), (n) -> "n=${n + 1}")))\n', 0, "n=2"),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
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
