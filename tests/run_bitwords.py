"""The word forms of the bit operators (`bit_and(a, b)` is `a & b`, and so on) behave exactly like the symbols.
Run: python3 tests/run_bitwords.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ("plain integers", 'println(bit_and(12, 10))\nprintln(bit_or(12, 10))\nprintln(bit_xor(12, 10))\nprintln(bit_not(0))\nprintln(shl(1, 4))\nprintln(shr(256, 4))\n', "8\n14\n6\n-1\n16\n16"),
 ("same as the symbols", 'println(bit_and(12, 10) == 12 & 10 and shl(3, 2) == 3 << 2 and shr(40, 3) == 40 >> 3 and bit_not(5) == ~5)\n', "true"),
 ("sized integers wrap like the operators", 'x UInt8 = 200\nprintln(shl(x, 1))\nprintln(bit_not(x))\nprintln(bit_and(x, 15))\n', "144\n55\n8"),
 ("in a pipe", 'println(12 |> bit_and(10))\n', "8"),
 ("a shift count out of range aborts", 'println(shl(1, 70))\n', "shift count out of range"),
]
fails = []
for name, src, want in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name], cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = (r.stdout + r.stderr).strip()
        ok = (want in o) if "shift count" in want else (o == want)
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> {o[:200]!r}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
