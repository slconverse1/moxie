#!/usr/bin/env python3
"""One documentation page per prelude function: docs/ref/NAME.md and docs/gc/ref/NAME.md, linked from the alphabetical list in the
Spec reference.  The text is written in tools/refdocs/*.py; each example is run through the interpreter here and the page shows
what it really printed, so an example can't claim a result the interpreter doesn't give.  Run: python3 tools/make_ref_pages.py"""
import glob, importlib.util, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import make_reference as mr

def load_docs():
    D = {}
    for f in sorted(glob.glob(os.path.join(HERE, "refdocs", "*.py"))):
        spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        for k, v in m.DOCS.items():
            if k in D: print("duplicate doc for", k)
            D[k] = v
    return D

def run_examples(name, exprs, gc):
    """Run each expression as `println(show(expr))`; return the printed line, or ERROR: and the message."""
    outs = []
    for e in exprs:
        src = "println(show(%s))\n" % e if "\n" not in e else e + "\n"
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "ex.mxi"); open(p, "w").write(src)
            cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", p]
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=30)
        out = r.stdout.rstrip("\n")
        if r.returncode != 0 or (r.stderr.strip() and not out):
            outs.append("ERROR: " + (r.stderr.strip().splitlines() or ["?"])[-1])
        else:
            outs.append(out)
    return outs

def page_text(name, gc, entry, results, S):
    text, examples, shown = entry
    dialect = "moxie/gc" if gc else "moxie"
    sec = next((s for _, s, items in mr.FUNCS for n, _ in items if n == name), None)
    out = ["---", "layout: default", "toc: true", "terms: true"]
    if gc: out.append("dialect: gc")
    out += ['title: "%s · %s function"' % (name, dialect), "---", ""]
    out.append("# `%s`" % name); out.append("")
    back = '<a href="../reference.html#fn-%s">The alphabetical list</a>' % name
    link = ' · <a href="../spec.html#%s">Spec §%s</a>' % (sec, sec[1:]) if sec else ""
    out.append('<p class="specref">%s%s</p>' % (back, link)); out.append("")
    out.append("## Signature {#signature}"); out.append("")
    out.append("```"); out.append(mr.full_sig(name, S)); out.append("```"); out.append("")
    out.append("## Description {#description}"); out.append("")
    out.append(text.strip("\n")); out.append("")
    eff = mr.effect_line(name)
    out.append("## Effects {#effects}"); out.append("")
    out.append((eff.replace("Effect: ", "**Effect:** ").replace(" · Needs permission:", "\n\n**Needs permission:**").replace("Needs permission: ", "**Needs permission:** ")
                if eff else "None: this function is pure.")); out.append("")
    if examples or shown:
        out.append("## Examples {#examples}"); out.append("")
        for (e, res) in zip(examples, results):
            out.append("```"); out.append("> " + e); out.append(res); out.append("```"); out.append("")
        for e, res in shown:
            out.append("```"); out.append("> " + e); out.append(res); out.append("```"); out.append("")
    return "\n".join(out)

def main():
    D = load_docs()
    S = mr.load_sigs()
    names = [n for _, _, items in mr.FUNCS for n, _ in items]
    missing = [n for n in names if n not in D]
    extra = [n for n in D if n not in names]
    if extra: print("docs for unknown functions:", " ".join(extra))
    todo = [n for n in names if n in D]
    def work(n):
        text, examples, shown = D[n]
        return n, run_examples(n, examples, False), run_examples(n, examples, True)
    bad = 0
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(work, todo))
    for n, r1, r2 in res:
        for e, a, b in zip(D[n][1], r1, r2):
            if a.startswith("ERROR") or b.startswith("ERROR") or a != b:
                bad += 1; print("EXAMPLE PROBLEM", n, "|", e, "|", a, "|", b)
        for gc, r in ((False, r1), (True, r2)):
            d = os.path.join(ROOT, "docs", "gc" if gc else "", "ref"); os.makedirs(d, exist_ok=True)
            open(os.path.join(d, n + ".md"), "w").write(page_text(n, gc, D[n], r, S) + "\n")
    print("pages for %d functions; %d without a page yet; %d example problems" % (len(todo), len(missing), bad))
    if missing and "--list" in sys.argv: print(" ".join(missing))
    open(os.path.join(HERE, "refdocs", ".done"), "w").write("\n".join(todo))

if __name__ == "__main__":
    main()
