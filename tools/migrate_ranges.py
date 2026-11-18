"""One-off: rewrite moxie source text from the old range spelling (`a..b` exclusive, `a..=b` inclusive) to the Kotlin one
(`a..b` inclusive, `a..<b` exclusive).  Run: python3 tools/migrate_ranges.py FILE...   (rewrites in place)"""
import re, sys

PAT = re.compile(r"(?<![.])(\.\.=|\.\.)(?![.])")

def fix(text):
    out, last = [], 0
    for m in PAT.finditer(text):
        i, j = m.span()
        if m.group(1) == "..=":
            rep = ".."
        else:
            nx = text[j:j + 1]
            word = re.match(r"step\b", text[j:j + 5])
            if nx and (nx.isalnum() or nx in "_($'\"-") and not word:
                rep = "..<"
            else:
                rep = ".."
        out.append(text[last:i]); out.append(rep); last = j
    out.append(text[last:])
    return "".join(out)

if __name__ == "__main__":
    for p in sys.argv[1:]:
        s = open(p, encoding="utf-8").read()
        if p.endswith(".py"):
            s2 = "".join(fix(l) if "os.path" not in l and "'..'" not in l else l for l in s.splitlines(True))
        else:
            s2 = fix(s)
        if s2 != s:
            open(p, "w", encoding="utf-8").write(s2)
            print("migrated", p)
