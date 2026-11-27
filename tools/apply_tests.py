import ast, re, sys, glob
sys.path.insert(0, "/tmp/ffb/tools")
from bare_convert import convert
LIT = re.compile(r"'(?:[^'\\\n]|\\.)*'")
def enc(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"
total = 0
for f in sys.argv[1:]:
    src = open(f, encoding="utf-8").read()
    def rep(m):
        global total
        lit = m.group(0)
        if "(\\n" not in lit:
            return lit
        try:
            val = ast.literal_eval(lit)
        except Exception:
            return lit
        if "(\n" not in val:
            return lit
        new, sk = convert(val)
        if new == val:
            return lit
        total += 1
        return enc(new)
    out = LIT.sub(rep, src)
    if out != src:
        open(f, "w", encoding="utf-8").write(out); print("updated", f)
print("literals changed:", total)
