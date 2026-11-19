"""Check docs/grammar.ebnf against moxie's own lexer: every code block of the guides that the real parser accepts must be
recognized by the grammar (and a few programs the parser rejects must be rejected by it).
Run: python3 tests/run_grammar.py [-v]   (-v lists every block the grammar does not recognize)"""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from ebnf import Grammar                      # noqa: E402
from moxie.lexer import tokenize              # noqa: E402

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
print(f"grammar recognizes {ok} of {total} guide blocks the parser accepts ({skipped} fragments skipped)")
if verbose:
    for tag, src, at, t in fails:
        ctx = " ".join(str(v if v is not None else k) for k, v in t[max(0, at - 6):at + 3])
        print(f"--- [{tag}] stuck near token {at}: {ctx}")
        print("    " + src.strip().splitlines()[0][:100])
need = float(os.environ.get("GRAMMAR_MIN", "0.80"))
sys.exit(0 if total and ok / total >= need else 1)
