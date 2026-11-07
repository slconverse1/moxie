"""Checker gaps: repeated type parameters in builtins, mixed-type collection literals, lambda arity."""
import sys, subprocess
BAD = [
 ("a: Result[String, String] = Ok(\"x\")\nb: Result[String, Int] = Ok(\"y\")\nq = map_all((x, y): x, a, b)\n", "repeated type parameter"),
 ("xs = List(1, \"a\")\n", "must share one type"),
 ("xs: List[Int] = List(1, \"a\")\n", "must share one type"),
 ("a: Result[Int, String] = Ok(1)\nb: Result[Int, Int] = Ok(2)\nxs = List(a, b)\n", "must share one type"),
 ("x = List(1, 2).map((a, b): a)\n", "takes 2 parameters"),
 ("x = reduce(0, (a): a, List(1, 2))\n", "takes 1 parameter"),
 ("x = Ok(1).map((a, b): a)\n", "takes 2 parameters"),
 ("d: Dict[Int, Int] = Dict(1: 2)\nx = d |> map((a, b, c): a)\n", "takes 3 parameters"),
 ("x = List((1, 2)).map((a, b, c): a)\n", "takes 3 parameters"),
 ("x = List(1, 2).filter((a, b): true)\n", "takes 2 parameters"),
 ("x = map_all((a, b, c): a, Ok(1), Ok(2))\n", "takes 3"),
]
GOOD = [
 "enum Shape:\n  Circle(r: Int)\n  Sq(s: Int)\nxs = List(Circle(1), Sq(2))\nys = List(1, 2.5)\nzs = List(Ok(1), Err(\"x\"))\nprintln(len(xs) + len(ys) + len(zs))\n",
 "x = List(1, 2).map((a): a + 1) |> collect()\nprintln(x)\n",
 "x = reduce(0, (a, b): a + b, List(1, 2))\nprintln(x)\n",
 "d: Dict[Int, Int] = Dict(1: 2)\nx = d |> map((k, v): k) |> collect()\nprintln(x)\n",
 "x = List((1, 2)).map((a, b): a) |> collect()\nprintln(x)\n",
 "x = Ok((1, 2)).map((a, b): a)\nprintln(x)\n",
 "x = Ok(1).map((a): a + 1)\nprintln(x)\n",
]
fails = 0
def chk(src, *flags):
    open("/tmp/_gap.mx", "w").write(src)
    return subprocess.run([sys.executable, "-m", "moxie", *flags, "check", "/tmp/_gap.mx"], capture_output=True, text=True)
for flags in ((), ("--gc",)):
    for src, msg in BAD:
        r = chk(src, *flags)
        if msg not in r.stdout + r.stderr:
            fails += 1; print("FAIL bad", flags, repr(src), r.stdout, r.stderr)
    for src in GOOD:
        r = chk(src, *flags)
        if r.returncode:
            fails += 1; print("FAIL good", flags, repr(src), r.stdout, r.stderr)
print("checker gaps: FAIL" if fails else "checker gaps: ok")
