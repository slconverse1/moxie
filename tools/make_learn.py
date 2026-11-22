"""Builds the teaching guide ("Learning Guide") for both dialects from one source, lessons/.

lessons/_toc.txt lists the course:  a line `# Part title` starts a part; every other non-blank line is a lesson file name
(without .md).  A lesson starts with `# Title`.  In a lesson:
  @gc ... @end      text kept only in the moxie/gc pages
  @nogc ... @end    text kept only in the GC-free pages
  ```moxie          a self-contained example, checked by tests/run_learn.py
  ```output         the exact output of the example above it (checked)
  ```error          a substring of the compile or run-time error the example above it must print
  ```moxie-nocheck  a snippet that is shown but not run
Writes docs/learn/ and docs/gc/learn/ (one page per lesson, plus an index).   Run: python3 tools/make_learn.py
"""
import os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "lessons")


def toc():
    parts, cur = [], None
    for line in open(os.path.join(SRC, "_toc.txt"), encoding="utf-8").read().split("\n"):
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("# "):
            cur = (line[2:].strip(), [])
            parts.append(cur)
        else:
            cur[1].append(line)
    return parts


def dialect_text(text, gc):
    """Apply @gc / @nogc ... @end."""
    out, keep, stack = [], True, None
    for line in text.split("\n"):
        s = line.strip()
        if s in ("@gc", "@nogc"):
            assert stack is None, "nested @gc/@nogc"
            stack = s
            keep = (s == "@gc") == gc
        elif s == "@end":
            assert stack is not None, "@end without @gc/@nogc"
            stack, keep = None, True
        elif keep:
            out.append(line)
    assert stack is None, "unterminated @gc/@nogc"
    return "\n".join(out)


def title_of(text):
    m = re.match(r"# (.+)", text)
    assert m, "a lesson starts with # Title"
    return m.group(1).strip()


def render(text, gc):
    text = dialect_text(text, gc)
    text = re.sub(r"^```moxie\n//! file: (\S+)\n", lambda mm: f"**`{mm.group(1)}`**\n\n```moxie\n", text, flags=re.M)   # a supporting file is shown with its name
    text = re.sub(r"^//! .*\n", "", text, flags=re.M)             # directives for the test runner
    text = re.sub(r"^```moxie-nocheck$", "```moxie", text, flags=re.M)
    text = re.sub(r"^```output$", "**Output:**\n\n```", text, flags=re.M)
    text = re.sub(r"^```error$", "**The compiler says:**\n\n```", text, flags=re.M)
    return text


def lessons():
    """[(part title, [(slug, title, source text)])]"""
    out = []
    for ptitle, names in toc():
        ls = []
        for n in names:
            t = open(os.path.join(SRC, n + ".md"), encoding="utf-8").read()
            ls.append((n, title_of(t), t))
        out.append((ptitle, ls))
    return out


def build(gc):
    base = os.path.join(ROOT, "docs", "gc", "learn") if gc else os.path.join(ROOT, "docs", "learn")
    shutil.rmtree(base, ignore_errors=True)
    os.makedirs(base)
    name = "moxie/gc" if gc else "moxie"
    parts = lessons()
    flat = [(p, s, t, txt) for p, ls in parts for (s, t, txt) in ls]
    dia = ("dialect: gc\n" if gc else "") + "learn: true\n"
    # the sidebar: one list per dialect, in docs/_includes, shared by every lesson page
    nav = ["<ul>"]
    k = 0
    for p, ls in parts:
        nav.append(f'<li class="part">{p}</li>')
        for s, t, _ in ls:
            k += 1
            nav.append(f'<li><a href="{s}.html">{k}. {t}</a></li>')
    nav.append("</ul>")
    inc = os.path.join(ROOT, "docs", "_includes")
    os.makedirs(inc, exist_ok=True)
    open(os.path.join(inc, "learn-nav-gc.html" if gc else "learn-nav.html"), "w", encoding="utf-8").write("\n".join(nav) + "\n")
    idx = [f"---\nlayout: default\n{dia}title: \"Learning Guide {name}\"\n---\n# LEARNING GUIDE {name.upper()}\n"]
    idx.append(open(os.path.join(SRC, "_intro.md"), encoding="utf-8").read().strip().replace("{{name}}", name) + "\n")
    n = 0
    for p, ls in parts:
        idx.append(f"\n## {p}\n")
        for s, t, _ in ls:
            n += 1
            idx.append(f"{n}. [{t}]({s}.html)")
    open(os.path.join(base, "index.md"), "w", encoding="utf-8").write("\n".join(idx) + "\n")
    for i, (p, s, t, txt) in enumerate(flat):
        body = render(txt, gc)
        body = re.sub(r"^# (.+)$", lambda m: f"# {i + 1}. {m.group(1)}", body, 1, flags=re.M)
        nv = []
        if i > 0:
            nv.append(f"[← {flat[i - 1][2]}]({flat[i - 1][1]}.html)")
        nv.append("[Contents](./)")
        if i + 1 < len(flat):
            nv.append(f"[{flat[i + 1][2]} →]({flat[i + 1][1]}.html)")
        page = f"---\nlayout: default\n{dia}title: \"{t} · Learning Guide {name}\"\n---\n<p><small>{p}</small></p>\n\n{body.rstrip()}\n\n---\n\n" + " · ".join(nv) + "\n"
        open(os.path.join(base, s + ".md"), "w", encoding="utf-8").write(page)
    return len(flat)


if __name__ == "__main__":
    for gc in (False, True):
        print(("gc  " if gc else "no-gc ") + str(build(gc)) + " lessons")
