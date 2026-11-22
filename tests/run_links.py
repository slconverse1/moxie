"""Guide and Spec cross-links: every lesson and Spec section is mapped, and every link resolves.  Run: python3 tests/run_links.py"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_learn as ml, link_spec as ls
fails = []
def chk(name, cond):
    print(("ok    " if cond else "FAIL  ") + name)
    if not cond: fails.append(name)
m = ls.mapping()
slugs = [s for _, l in ml.lessons() for s, _, _ in l]
chk("every lesson is mapped", [s for s in slugs if s not in m] == [])
chk("no mapping for a missing lesson", [s for s in m if s not in slugs] == [])
heads = re.findall(r"^## \S+\. .+? \{#(s\w+)\}", open(os.path.join(ROOT, "docs/spec.md")).read(), re.M)
chk("every Spec section is mapped", [h for h in heads if not any(h in v for v in m.values())] == [])
chk("mapped sections exist", [x for v in m.values() for x in v if x not in heads] == [])
for d, spec in (("docs", "docs/spec.md"), ("docs/gc", "docs/gc/spec.md")):
    t = open(os.path.join(ROOT, spec)).read()
    ids = set(re.findall(r"\{#(s\w+)\}", t))
    bad = [l for l in re.findall(r"\]\((learn/[^)]+\.html)\)", t) if not os.path.exists(os.path.join(ROOT, d, l.replace(".html", ".md")))]
    chk(f"{spec}: guide links resolve", bad == [] and "<!-- guide -->" in t)
    pages = [f for f in os.listdir(os.path.join(ROOT, d, "learn")) if f.endswith(".md") and f != "index.md"]
    bad = []
    for f in pages:
        for sid in re.findall(r"\(\.\./spec\.html#(s\w+)\)", open(os.path.join(ROOT, d, "learn", f)).read()):
            if sid not in ids: bad.append((f, sid))
    chk(f"{d}/learn: Spec links resolve", bad == [])
    stale = [f for f in pages if "In the Spec:" not in open(os.path.join(ROOT, d, "learn", f)).read()]
    chk(f"{d}/learn: every lesson has a Spec line", stale == [])
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
