"""Check docs/grammar.ebnf against moxie's own lexer: every code block of the guides that the real parser accepts must be
recognized by the grammar (and a few programs the parser rejects must be rejected by it).
Run: python3 tests/run_grammar.py [-v]   (-v lists every block the grammar does not recognize)"""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from ebnf import Grammar                      # noqa: E402
from moxie.lexer import tokenize              # noqa: E402

def spec_has_grammar(path):
    text = open(os.path.join(ROOT, "docs", path)).read()
    return "```\n" + open(os.path.join(ROOT, "docs", "grammar.ebnf")).read().rstrip("\n") + "\n```" in text

stale = [p for p in ("spec.md", os.path.join("gc", "spec.md")) if not spec_has_grammar(p)]
for p in stale:
    print(f"docs/{p} does not contain the current docs/grammar.ebnf in section 26")
if stale:
    sys.exit(1)
verbose = "-v" in sys.argv
G = Grammar(open(os.path.join(ROOT, "docs", "grammar.ebnf")).read())

def toks(src):
    return [(t.kind, t.val) for t in tokenize(src, "t")]

def parses(src):
    """True when moxie's own parser accepts the source."""
    try:
        from moxie.parser import parse_program
        parse_program(src, "t")
        return True
    except BaseException:
        return False

blocks = []
for f in ("guide_corpus.json", "gc_guide_corpus.json"):
    for c in json.load(open(os.path.join(ROOT, "tests", f))):
        blocks.append((f[:2], c[1]))
import glob
def battery(path):
    """Programs of a tests/battery file: '### name', a verdict line ('ok...' / 'reject...'), then the source."""
    out, cur, first = [], None, False
    for line in open(path).read().split("\n"):
        if line.startswith("### "):
            if cur is not None:
                out.append("\n".join(cur) + "\n")
            cur, first = [], True
        elif cur is not None:
            if first:
                first = False
                continue
            cur.append(line)
    if cur is not None:
        out.append("\n".join(cur) + "\n")
    return out
for f in sorted(glob.glob(os.path.join(ROOT, "examples", "*.mxi")) + glob.glob(os.path.join(ROOT, "moxie", "std", "*.mxi"))
                + glob.glob(os.path.join(ROOT, "moxie", "std", "*", "*.mxi"))):
    blocks.append(("ex", open(f).read()))
for f in sorted(glob.glob(os.path.join(ROOT, "tests", "battery", "*.txt"))):
    for src in battery(f):
        blocks.append(("ba", src))
seen, uniq = set(), []
for tag, src in blocks:
    if src not in seen:
        seen.add(src)
        uniq.append((tag, src))

ok = bad = skipped = 0
fails = []
for tag, src in uniq:
    if not parses(src):
        skipped += 1                    # a fragment the parser itself does not take on its own
        continue
    t = toks(src)
    good, at = G.recognize(t)
    if good:
        ok += 1
    else:
        bad += 1
        fails.append((tag, src, at, t))
total = ok + bad
print(f"grammar recognizes {ok} of {total} programs the parser accepts (guide blocks, examples, std library, battery) ({skipped} fragments skipped)")
if verbose:
    for tag, src, at, t in fails:
        ctx = " ".join(str(v if v is not None else k) for k, v in t[max(0, at - 6):at + 3])
        print(f"--- [{tag}] stuck near token {at}: {ctx}")
        print("    " + src.strip().splitlines()[0][:100])
# a grammar that accepts everything proves nothing: these are rejected by the parser, and must be by the grammar
BAD = ["x = = 1\n", "x = (1\n", "fn\n", "if\n", "x = 1 +\n", "when x\n", "for x in\n", "tuple\n", "enum\n", "x = )\n",
       "fn f(a Int b Int) Int = a\n", "x = List(1,, 2)\n", "fn f() Int =\n", "import\n", "x |> \n", "1 = x\n"]
wrong = []
for src in BAD:
    if parses(src):
        continue
    good, _at = G.recognize(toks(src))
    if good:
        wrong.append(src)
print(f"grammar rejects {len(BAD) - len(wrong)} of {len(BAD)} malformed programs the parser rejects")
for src in wrong:
    print("  accepted by the grammar but not by the parser:", repr(src))
if wrong:
    sys.exit(1)
need = float(os.environ.get("GRAMMAR_MIN", "1.0"))
sys.exit(0 if total and ok / total >= need else 1)
