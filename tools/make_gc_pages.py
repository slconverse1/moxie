"""Builds docs/gc/try.html and docs/gc/repl.html from docs/try.html and docs/repl.html, so the moxie/gc site has its own Try and REPL pages
(its own nav, titles, and links, with the gc rules ticked).  Run after editing either page:  python3 tools/make_gc_pages.py"""
import os, re
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
GC_NAV = ('<nav id="nav"><a href="./">moxie/gc</a><a href="tutorial.html">Tutorial</a><a href="guide.html">Mixer\'s Guide</a><a href="spec.html">Spec</a>'
          '<a href="../style.html">Style</a><a href="try.html">Try moxie/gc</a><a href="repl.html">REPL</a><a href="https://github.com/slconverse1/moxie">Source</a></nav>')

def sub(t, old, new, n=1):
    assert t.count(old) >= 1, old
    return t.replace(old, new, n)

for page, title in (("try.html", "Try moxie/gc"), ("repl.html", "moxie/gc REPL")):
    t = open(os.path.join(D, page)).read()
    t = re.sub(r"<nav id=\"nav\">.*?</nav>", GC_NAV, t, 1, flags=re.S)
    t = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", t, 1)
    t = re.sub(r"<h1>.*?</h1>", f"<h1>{title}</h1>", t, 1)
    t = sub(t, "new URL('moxie.zip', location.href)", "new URL('../moxie.zip', location.href)")
    t = sub(t, '<input type="checkbox" id="gc">', '<input type="checkbox" id="gc" checked>')
    if page == "try.html":
        t = sub(t, "fetch('samples/'", "fetch('../samples/'")
        t = sub(t, "new Worker('try-worker.js')", "new Worker('../try-worker.js')")
        t = sub(t, 'Tick "moxie/gc rules" to run it under the garbage-collected language (collections grow as needed).',
                'It runs under the moxie/gc rules (collections grow as needed); untick "moxie/gc rules" to see it under no-GC moxie.')
    else:
        t = sub(t, "new Worker('repl-worker.js')", "new Worker('../repl-worker.js')")
        t = sub(t, "Try <code>:help</code>.", "It runs under the moxie/gc rules; untick the box to start a no-GC session. Try <code>:help</code>.")
    open(os.path.join(D, "gc", page), "w").write(t)
print("wrote docs/gc/try.html and docs/gc/repl.html")
