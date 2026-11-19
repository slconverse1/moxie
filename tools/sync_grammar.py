"""Copy docs/grammar.ebnf into section 26 of both specs (the fenced block after "**26. Grammar**").  Run after editing the grammar."""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = open(os.path.join(ROOT, "docs", "grammar.ebnf")).read().rstrip("\n")
for p in ("spec.md", os.path.join("gc", "spec.md")):
    path = os.path.join(ROOT, "docs", p)
    s = open(path).read()
    i = s.index("**26. Grammar**")
    a = s.index("```\n", i) + 4
    b = s.index("\n```", a)
    s = s[:a] + g + s[b:]
    open(path, "w").write(s)
print("synced")
