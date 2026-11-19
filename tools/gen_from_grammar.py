"""Random programs from docs/grammar.ebnf, fed to moxie's own parser (the grammar checked from the other side).

tests/run_grammar.py asks "does the grammar recognize what the parser accepts"; this asks "does the parser accept what the
grammar generates".  A program the grammar makes and the parser refuses is a place where the grammar is looser than the
language (the checker settles names and types, so those are fine; the parser settles shape).

    python3 tools/gen_from_grammar.py [-n COUNT] [-s SEED] [-v]
"""
import glob, os, random, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from ebnf import Grammar                         # noqa: E402
from moxie.lexer import tokenize, Tok            # noqa: E402

NAMES = ["a", "b", "c", "f", "g", "x", "y", "n", "xs", "Foo", "Bar", "T", "U"]


def load_samples():
    """One real token of each literal kind, taken from the sources the repo already has."""
    seen = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "examples", "*.mxi"))) + glob.glob(os.path.join(ROOT, "moxie", "std", "*.mxi")):
        try:
            for t in tokenize(open(f).read(), f):
                if t.kind in ("INT", "FLOAT", "STR", "CHAR", "DEC", "DUR", "BYTES", "SQL", "HASH", "BTICK"):
                    seen.setdefault(t.kind, []).append(t)
        except Exception:
            pass
    return seen


class Gen:
    def __init__(self, grammar, rng, samples):
        self.g, self.rng, self.samples = grammar, rng, samples
        self.cost = self._costs()

    def _costs(self):
        """Fewest terminals each nonterminal can derive; picks the way out when a derivation gets deep."""
        cost = {nt: 10 ** 6 for nt in self.g.bnf}
        changed = True
        while changed:
            changed = False
            for nt, prods in self.g.bnf.items():
                for p in prods:
                    c = sum(cost[s[1]] if s[0] == "nt" else 1 for s in p)
                    if c < cost[nt]:
                        cost[nt] = c
                        changed = True
        return cost

    def derive(self, nt, depth, out):
        prods = self.g.bnf[nt]
        if depth > 14 or len(out) > 400:
            best = min(range(len(prods)), key=lambda i: sum(self.cost[s[1]] if s[0] == "nt" else 1 for s in prods[i]))
            prod = prods[best]
        else:
            prod = self.rng.choice(prods)
        for s in prod:
            k = s[0]
            if k == "nt":
                self.derive(s[1], depth + 1, out)
            elif k == "lit":
                out.append(Tok("NAME" if s[1][:1].isalpha() else "OP", s[1], 1, 0))
            elif k == "ident":
                out.append(Tok("NAME", self.rng.choice(NAMES), 1, 0))
            else:
                kind = s[1]
                if kind in ("NL", "INDENT", "DEDENT", "EOF"):
                    out.append(Tok(kind, None, 1, 0))
                elif kind == "NAME":
                    out.append(Tok("NAME", self.rng.choice(NAMES), 1, 0))
                elif self.samples.get(kind):
                    t = self.rng.choice(self.samples[kind])
                    n = Tok(t.kind, t.val, 1, 0)
                    n.extra = t.extra
                    out.append(n)
                else:
                    out.append(Tok(kind, "1", 1, 0))

    def program(self):
        out = []
        self.derive("program", 0, out)
        return fix(out)


def fix(toks):
    """Spacing and line numbers the lexer would have given: tight around brackets, calls and dots."""
    prev = None
    line = 1
    for t in toks:
        if t.kind == "NL":
            line += 1
        t.line = line
        tight = False
        if t.kind == "OP" and t.val in (")", "]", ",", ".", "?", ":", "}"):
            tight = True
        elif t.kind == "OP" and t.val in ("(", "[") and prev is not None and (
                prev.kind == "NAME" or (prev.kind == "OP" and prev.val in (")", "]"))):
            tight = True
        elif prev is not None and prev.kind == "OP" and prev.val in ("(", "[", ".", "@", "\\"):
            tight = True
        t.sp = not tight
        prev = t
    return toks


def render(toks):
    out, ind, line = [], 0, []
    for t in toks:
        if t.kind == "INDENT":
            ind += 1
        elif t.kind == "DEDENT":
            ind -= 1
        elif t.kind == "NL":
            out.append("  " * ind + " ".join(line))
            line = []
        elif t.kind == "EOF":
            pass
        else:
            line.append(str(t.val if t.val is not None else t.kind))
    if line:
        out.append("  " * ind + " ".join(line))
    return "\n".join(out)


def accepted(toks, file="gen"):
    from moxie.parser import Parser
    try:
        Parser(list(toks), file).parse_module()
        return True, ""
    except BaseException as e:                       # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def main():
    args = sys.argv[1:]
    n = int(args[args.index("-n") + 1]) if "-n" in args else 300
    seed = int(args[args.index("-s") + 1]) if "-s" in args else 1
    verbose = "-v" in args
    G = Grammar(open(os.path.join(ROOT, "docs", "grammar.ebnf")).read())
    gen = Gen(G, random.Random(seed), load_samples())
    ok = 0
    bad = []
    for _ in range(n):
        toks = gen.program()
        good, why = accepted(toks)
        if good:
            ok += 1
        else:
            bad.append((why, render(toks)))
    print(f"parser accepts {ok} of {n} programs the grammar generated (seed {seed})")
    if verbose:
        from collections import Counter
        c = Counter(w.split(" at ")[0][:90] for w, _ in bad)
        for w, k in c.most_common(25):
            print(f"{k:5}  {w}")
        for w, src in bad[:6]:
            print("-----", w[:120])
            print(src[:300])
    return ok, n


if __name__ == "__main__":
    main()
