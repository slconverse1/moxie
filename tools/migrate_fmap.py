"""One-off: inside `impl ... Functor/Applicative/Monad[...]` blocks, the Functor method `map` becomes `fmap`.
Run: python3 tools/migrate_fmap.py FILE...   (rewrites in place)"""
import re, sys

HEAD = re.compile(r"impl(\[[^\]\n]*\])? (Monad|Functor|Applicative)\[")
BOUND = re.compile(r"(?:\n|\\n)(?=[A-Za-z`#/@])")

def fix(text):
    out, pos = [], 0
    for m in HEAD.finditer(text):
        if m.start() < pos:
            continue
        nl = re.compile(r"\n|\\n").search(text, m.end())
        if nl is None:
            continue
        b = BOUND.search(text, nl.end())
        end = b.start() if b else len(text)
        span = text[m.start():end]
        new = re.sub(r"\bfn map\b", "fn fmap", span)
        new = re.sub(r"\.map\(", ".fmap(", new)
        out.append(text[pos:m.start()]); out.append(new); pos = end
    out.append(text[pos:])
    return "".join(out)

if __name__ == "__main__":
    for p in sys.argv[1:]:
        s = open(p, encoding="utf-8").read()
        s2 = fix(s)
        if s2 != s:
            open(p, "w", encoding="utf-8").write(s2)
            print("migrated", p)
