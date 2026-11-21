"""Set algebra: `-` difference, `&` intersection, `^` symmetric difference, and is_subset / is_superset / is_disjoint.  Run: python3 tests/run_setalgebra.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, gc=False):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
S = "a = Set(1, 2, 3)\nb = Set(2, 3, 4)\n"
CASES = [
 ("union is still +", S + "println(a + b)\n", "Set(1, 2, 3, 4)"),
 ("difference", S + "println(a - b)\n", "Set(1)"),
 ("intersection", S + "println(a & b)\n", "Set(2, 3)"),
 ("symmetric difference", S + "println(a ^ b)\n", "Set(1, 4)"),
 ("removing one element", S + "println(a - 1)\n", "Set(2, 3)"),
 ("is_subset", S + "println(is_subset(Set(2, 3), a))\nprintln(is_subset(b, a))\n", "true\nfalse"),
 ("is_superset", S + "println(is_superset(a, Set(1)))\n", "true"),
 ("is_disjoint", S + "println(is_disjoint(a, Set(9)))\nprintln(is_disjoint(a, b))\n", "true\nfalse"),
 ("a wrong element type is an error", S + "bad = a - \"x\"\n", "cannot apply `-` to a `Set[Int]` and a `String`"),
 ("in a pipeline", S + "println(a |> is_subset(Set(1, 2, 3, 4)))\n", "true"),
 ("Int bitwise & is unchanged", "println(6 & 3)\nprintln(6 ^ 3)\n", "2\n5"),
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
