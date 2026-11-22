"""Writes the "Guide:" line under each Spec heading (docs/spec.md, docs/gc/spec.md) from lessons/_spec.txt.
The line sits between <!-- guide --> and <!-- /guide --> so it can be regenerated.   Run: python3 tools/link_spec.py"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_learn as ml
ROOT = ml.ROOT


def mapping():
    m = {}
    for l in open(os.path.join(ml.SRC, "_spec.txt"), encoding="utf-8"):
        l = l.strip()
        if l and not l.startswith("//"):
            k, v = l.split(":", 1)
            m[k.strip()] = [x.strip() for x in v.split(",")]
    return m


def lesson_numbers():
    """slug -> (display number, title)"""
    out, k = {}, 0
    for _, ls in ml.lessons():
        for s, t, _ in ls:
            k += 1
            out[s] = (k, t)
    return out


def link(spec):
    path = os.path.join(ROOT, "docs", "gc", "spec.md") if spec else None
    return path


def run():
    nums, m = lesson_numbers(), mapping()
    bysec = {}
    for slug, secs in m.items():
        for s in secs:
            bysec.setdefault(s, []).append(slug)
    for path in (os.path.join(ROOT, "docs", "spec.md"), os.path.join(ROOT, "docs", "gc", "spec.md")):
        t = open(path, encoding="utf-8").read()
        t = re.sub(r"<!-- guide -->.*?<!-- /guide -->\n\n?", "", t, flags=re.S)
        def add(mm):
            sid = mm.group(2)
            slugs = sorted(bysec.get(sid, []), key=lambda s: nums[s][0])
            if not slugs:
                return mm.group(0)
            links = ", ".join(f"[{nums[s][0]}. {nums[s][1]}](learn/{s}.html)" for s in slugs)
            return f"{mm.group(0)}\n<!-- guide -->\n*In the Learning Guide: {links}*\n<!-- /guide -->\n"
        t = re.sub(r"^(## \S+\. .+? \{#(s\w+)\})\n", lambda mm: add(mm) , t, flags=re.M)
        open(path, "w", encoding="utf-8").write(t)


if __name__ == "__main__":
    run()
