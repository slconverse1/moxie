"""Grapheme clusters: graphemes(s) and grapheme_count(s).  Run: python3 tests/run_graphemes.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from moxie.graphemes import split

fails = []
def ok(name, good, detail=""):
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  {detail}"))
    if not good: fails.append(name)

CASES = [
 ("empty", "", 0), ("plain letters", "ab", 2), ("letter and combining accent", "é", 1),
 ("accent then letter", "éx", 2), ("CR LF is one", "\r\n", 1), ("LF CR is two", "\n\r", 2),
 ("a flag", "\U0001F1FA\U0001F1F8", 1), ("two flags", "\U0001F1FA\U0001F1F8\U0001F1EB\U0001F1F7", 2),
 ("an odd regional indicator", "\U0001F1FA\U0001F1F8\U0001F1EB", 2),
 ("a family joined by ZWJ", "\U0001F468‍\U0001F469‍\U0001F467", 1),
 ("a skin tone modifier", "\U0001F44D\U0001F3FD", 1), ("a thumb then a thumb", "\U0001F44D\U0001F3FD\U0001F44D", 2),
 ("Hangul jamo L V T", "각", 1), ("a Hangul syllable", "각", 1), ("two syllables", "각각", 2),
 ("ZWJ between letters does not join", "a‍b", 2), ("a variation selector", "❤️", 1),
 ("a rainbow flag", "\U0001F3F3️‍\U0001F308", 1), ("Devanagari with a vowel sign", "नमस्ते", 4),
]
for name, s, n in CASES:
    g = split(s)
    ok(name, len(g) == n and "".join(g) == s, f"got {len(g)} {g!r}")

def run(src):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    return r.returncode, r.stdout.decode() + r.stderr.decode()

rc, out = run('s = "e\\u{0301}\U0001F1FA\U0001F1F8\U0001F468\\u{200d}\U0001F469\\u{200d}\U0001F467a"\nprintln(len(s))\nprintln(char_count(s))\nprintln(grapheme_count(s))\nprintln(s |> graphemes() |> count())\n')
ok("the three lengths differ", rc == 0 and out.split() == ["30", "10", "4", "4"], out)
rc, out = run('for g in graphemes("e\\u{0301}!"):\n  println(len(g))\n')
ok("graphemes gives one String per cluster", rc == 0 and out.split() == ["3", "1"], out)
print()
print("FAILURES: " + ", ".join(fails) if fails else "all grapheme tests passed")
sys.exit(1 if fails else 0)
