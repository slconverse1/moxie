"""One-off: drop `to_stream()` from the start of pipelines (every collection, range and string is a source now).
Run: python3 tools/migrate_to_stream.py FILE...   (rewrites in place)"""
import re, sys

def fix(t):
    t = re.sub(r"\|> to_stream\(\) \|> ", "|> ", t)
    t = re.sub(r"\|> to_stream\(\)(\s*)\|> ", r"|> ", t) if False else t
    t = re.sub(r"\.to_stream\(\)\.", ".", t)
    t = re.sub(r"(\n|\\n)(\s*)\|> to_stream\(\)(?=(\n|\\n)\s*\|>)", "", t)
    return t

if __name__ == "__main__":
    for p in sys.argv[1:]:
        s = open(p, encoding="utf-8").read()
        s2 = fix(s)
        if s2 != s:
            open(p, "w", encoding="utf-8").write(s2)
            print("migrated", p)
