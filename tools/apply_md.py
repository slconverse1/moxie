import glob, re, sys
sys.path.insert(0, "/tmp/ffb/tools")
from bare_convert import convert
FENCE = re.compile(r"(?m)^( *)```(moxie)\n(.*?)\n\1```", re.S)
files = sys.argv[1:]
report = []
for f in files:
    s = open(f, encoding="utf-8").read()
    def rep(m):
        ind, lang, body = m.group(1), m.group(2), m.group(3)
        lines = [x[len(ind):] if x.startswith(ind) else x for x in body.split("\n")]
        code = "\n".join(lines)
        try:
            new, sk = convert(code)
        except Exception as e:
            report.append((f, "EXC", str(e)[:100])); return m.group(0)
        for ln, why in sk:
            report.append((f, ln, why))
        new_lines = [(ind + x) if x.strip() else x for x in new.split("\n")]
        return m.group(0)[: m.start(3) - m.start(0)] + "\n".join(new_lines) + "\n" + ind + "```"
    s2 = FENCE.sub(rep, s)
    if s2 != s:
        open(f, "w", encoding="utf-8").write(s2); print("updated", f)
for r in report: print("SKIP", *r)
