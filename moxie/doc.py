"""moxie doc: documentation generator.

Reads `///` doc comments (and `//!` module comments), the contract lines
(`requires` / `ensures` / `invariant`), and checks the `> expr` examples in the
doc text as doctests.  Output is static HTML (default) or Markdown.

The interpreter does not parse or enforce contracts yet, so the contract lines
are blanked out before parsing (keeping line numbers) and collected as text.
"""
import html
import io
import re

from .parser import parse_program

CONTRACT = re.compile(r"^(\s*)(requires|ensures|invariant)\b\s*(.*)$")
ITEM_NODES = ("FnDecl", "FnGroup", "TupleDecl", "EnumDecl", "IfaceDecl", "AliasDecl", "ImplDecl")
KIND = {"FnDecl": "fn", "FnGroup": "fn", "TupleDecl": "tuple", "EnumDecl": "enum",
        "IfaceDecl": "interface", "AliasDecl": "alias", "ImplDecl": "impl"}


class Item:
    def __init__(self, kind, name, line, header, exported):
        self.kind, self.name, self.line, self.header, self.exported = kind, name, line, header, exported
        self.doc = []          # doc text lines
        self.body = []         # nested declaration lines (tuple fields, enum cases, iface members)
        self.contracts = []    # (owner header text or None, keyword, condition)
        self.examples = []     # (expr, expected, source line)
        self.implementors = []


def indent_of(s):
    return len(s) - len(s.lstrip(" "))


def strip_contracts(src):
    """Blank contract lines; return (clean source, [(line_no, indent, keyword, cond)])."""
    lines, found = src.split("\n"), []
    for i, ln in enumerate(lines):
        m = CONTRACT.match(ln)
        if m and not ln.lstrip().startswith("//"):
            found.append((i + 1, len(m.group(1)), m.group(2), m.group(3).strip()))
            lines[i] = ""
    return "\n".join(lines), found


def header_text(lines, start):
    """Source header from line `start` (1-based) up to the line that ends with ':'."""
    out, i = [], start - 1
    while i < len(lines):
        t = lines[i].rstrip()
        out.append(t.strip())
        if t.endswith(":") or not t.strip():
            break
        if i + 1 < len(lines) and indent_of(lines[i + 1]) <= indent_of(lines[i]) and not t.endswith(("(", ",")):
            break
        i += 1
    h = " ".join(out)
    h = re.sub(r"\s*:$", "", h)
    return h


def block_after(lines, start):
    """Lines nested below the header at `start`, skipping blanks, comments and contracts."""
    base = indent_of(lines[start - 1])
    out = []
    for ln in lines[start:]:
        if ln.strip() and indent_of(ln) <= base:
            break
        if ln.strip() and not ln.strip().startswith("//") and not CONTRACT.match(ln):
            out.append(ln)
    return out


def doc_before(lines, line):
    """`///` lines directly above 1-based `line`."""
    out, i = [], line - 2
    while i >= 0 and lines[i].strip().startswith("///"):
        out.append(re.sub(r"^\s*/// ?", "", lines[i]))
        i -= 1
    return list(reversed(out))


def parse_examples(doc, line0):
    """`> expr` lines followed by their expected output."""
    ex, i = [], 0
    while i < len(doc):
        if doc[i].startswith("> "):
            expr, exp = doc[i][2:], []
            i += 1
            while i < len(doc) and doc[i].strip() and not doc[i].startswith("> "):
                exp.append(doc[i])
                i += 1
            ex.append((expr, "\n".join(exp), line0 + i))
        else:
            i += 1
    return ex


def collect(src):
    clean, contracts = strip_contracts(src)
    prog = parse_program(clean, "<doc>")
    lines = clean.split("\n")
    orig = src.split("\n")
    module_doc = [re.sub(r"^\s*//! ?", "", l) for l in orig if l.strip().startswith("//!")]
    items = []
    for st in prog.stmts:
        cn = st.__class__.__name__
        if cn not in ITEM_NODES:
            continue
        line = st.line
        name = getattr(st, "name", None)
        if cn == "ImplDecl":
            name = f"impl {getattr(st, 'iface', '')} for {getattr(st, 'target', '')}"
            name = re.sub(r"\s+", " ", header_text(lines, line))
        elif cn == "FnGroup" and st.clauses:
            line = st.clauses[0].line
        h = header_text(lines, line)
        exported = h.startswith("export ")
        h = re.sub(r"^export\s+", "", h)
        it = Item(KIND[cn], str(name), line, h, exported)
        it.doc = doc_before(orig, line)
        it.examples = parse_examples(it.doc, line - len(it.doc))
        if cn in ("TupleDecl", "EnumDecl", "IfaceDecl"):
            it.body = [l for l in block_after(lines, line)]
        items.append(it)
    # attach contracts to the item that owns them
    for ln, ind, kw, cond in contracts:
        owner = None
        for j in range(ln - 2, -1, -1):
            t = lines[j]
            if t.strip() and not t.strip().startswith("//") and indent_of(t) < ind:
                owner = j + 1
                break
        if owner is None:
            continue
        top = None
        for it in items:
            if it.line <= owner:
                top = it
        if top is None:
            continue
        label = None if owner == top.line else header_text(lines, owner)
        top.contracts.append((label, kw, cond))
    # implementors
    for it in items:
        if it.kind == "impl":
            m = re.match(r"impl\s+(\w+)", it.header)
            if m:
                for other in items:
                    if other.kind == "interface" and other.name == m.group(1):
                        other.implementors.append(it.header)
    return clean, module_doc, items


# ---------------------------------------------------------------- doctests

def _esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n")


def run_doctests(clean, items, make_interp):
    """Run every example; return a list of (item, expr, expected, ok, message)."""
    cases, tests = [], []
    for it in items:
        for expr, exp, ln in it.examples:
            name = f"doctest {it.name} line {ln}"
            tests.append(f'test "{name}":\n  assert_eq(show({expr}), "{_esc(exp)}")\n')
            cases.append((it, expr, exp, name))
    if not cases:
        return []
    src = clean + "\n" + "\n".join(tests)
    I = make_interp()
    buf = io.StringIO()
    I.out = buf
    I.run_tests(src, "<doctest>")
    status = {}
    for l in buf.getvalue().split("\n"):
        if l.startswith("ok    "):
            status[l[6:]] = (True, "")
        elif l.startswith("FAIL  "):
            nm, _, msg = l[6:].partition(": ")
            status[nm] = (False, msg)
    return [(it, e, x, *status.get(n, (False, "did not run"))) for it, e, x, n in cases]


# ---------------------------------------------------------------- rendering

def _inline(s):
    s = html.escape(s)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", s)


def md_to_html(lines):
    out, para, ul, code = [], [], False, None

    def flush():
        nonlocal para
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para = []
    for ln in lines:
        if code is not None:
            if ln.startswith("```"):
                out.append("<pre>" + html.escape("\n".join(code)) + "</pre>")
                code = None
            else:
                code.append(ln)
            continue
        if ln.startswith("```"):
            flush()
            code = []
        elif ln.startswith("> "):
            continue                    # examples are shown separately
        elif ln.startswith("- "):
            flush()
            if not ul:
                out.append("<ul>")
                ul = True
            out.append("<li>" + _inline(ln[2:]) + "</li>")
        else:
            if ul and not ln.startswith("  "):
                out.append("</ul>")
                ul = False
            if not ln.strip():
                flush()
            elif ln.startswith("# "):
                flush()
                out.append("<h4>" + _inline(ln[2:]) + "</h4>")
            elif not _is_expected(ln, lines):
                para.append(ln.strip())
    flush()
    if ul:
        out.append("</ul>")
    return "\n".join(out)


def _is_expected(ln, lines):
    """True when `ln` is the expected-output line of a `> expr` example."""
    i = lines.index(ln) if ln in lines else -1
    j = i - 1
    while j >= 0 and lines[j].strip():
        if lines[j].startswith("> "):
            return True
        j -= 1
    return False


def doc_text_lines(it):
    """Doc lines without the example blocks."""
    out, skip = [], False
    for ln in it.doc:
        if ln.startswith("> "):
            skip = True
            continue
        if skip and ln.strip():
            continue
        skip = False
        out.append(ln)
    return out


CSS = ("body{font:16px/1.5 system-ui,sans-serif;max-width:46rem;margin:0 auto;padding:1rem 16px}"
       "pre,code{font-family:ui-monospace,monospace;background:#f2f2f2}pre{padding:.5rem;overflow-x:auto}"
       "code{padding:0 .2em}.sig{font-weight:600}.c{margin:.3rem 0}.k{color:#555}"
       ".ok{color:#16803c}.bad{color:#b00020}h3{margin-top:2rem;border-top:1px solid #ccc;padding-top:.6rem}"
       "@media(prefers-color-scheme:dark){body{background:#161616;color:#eee}pre,code{background:#2a2a2a}.k{color:#aaa}}")


def render_html(title, module_doc, items, results):
    res = {}
    for it, e, x, ok, msg in results:
        res.setdefault(id(it), []).append((e, x, ok, msg))
    o = [f"<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
         f"<title>{html.escape(title)}</title><style>{CSS}</style><body><h1>{html.escape(title)}</h1>"]
    if module_doc:
        o.append(md_to_html(module_doc))
    for it in items:
        o.append(f'<h3 id="{html.escape(it.name)}"><span class=k>{it.kind}</span> {html.escape(it.name)}</h3>')
        o.append(f'<pre class=sig>{html.escape(it.header)}</pre>')
        o.append(md_to_html(doc_text_lines(it)))
        if it.body:
            o.append("<pre>" + html.escape("\n".join(it.body)) + "</pre>")
        if it.contracts:
            o.append("<p><b>Contracts</b></p>")
            for label, kw, cond in it.contracts:
                lab = f" <span class=k>({html.escape(label)})</span>" if label else ""
                o.append(f'<div class=c><code>{kw} {html.escape(cond)}</code>{lab}</div>')
        if it.implementors:
            o.append("<p><b>Implementors</b></p><ul>" + "".join(f"<li><code>{html.escape(i)}</code></li>" for i in it.implementors) + "</ul>")
        if res.get(id(it)):
            o.append("<p><b>Examples</b></p>")
            for e, x, ok, msg in res[id(it)]:
                mark = '<span class=ok>ok</span>' if ok else f'<span class=bad>FAILED: {html.escape(msg)}</span>'
                o.append(f"<pre>&gt; {html.escape(e)}\n{html.escape(x)}</pre><div class=k>{mark}</div>")
    return "\n".join(o)


def render_md(title, module_doc, items, results):
    res = {}
    for it, e, x, ok, msg in results:
        res.setdefault(id(it), []).append((e, x, ok, msg))
    o = [f"# {title}", ""]
    if module_doc:
        o += module_doc + [""]
    for it in items:
        o += [f"### {it.kind} `{it.name}`", "", "```", it.header, "```", ""]
        t = doc_text_lines(it)
        if any(l.strip() for l in t):
            o += t + [""]
        if it.body:
            o += ["```"] + it.body + ["```", ""]
        if it.contracts:
            o += ["**Contracts**", ""]
            for label, kw, cond in it.contracts:
                o.append(f"- `{kw} {cond}`" + (f" ({label})" if label else ""))
            o.append("")
        if it.implementors:
            o += ["**Implementors**", ""] + [f"- `{i}`" for i in it.implementors] + [""]
        if res.get(id(it)):
            o += ["**Examples**", ""]
            for e, x, ok, msg in res[id(it)]:
                o += ["```", f"> {e}", x, "```", "" if ok else f"FAILED: {msg}", ""]
    return "\n".join(o)


LINK = re.compile(r"\[`([^`]+)`\]")


def check_links(items, module_doc):
    names = {it.name for it in items}
    errs = []
    for it in items:
        for ln in it.doc:
            for m in LINK.finditer(ln):
                if m.group(1) not in names:
                    errs.append(f"{it.name}: broken link [`{m.group(1)}`]")
    for ln in module_doc:
        for m in LINK.finditer(ln):
            if m.group(1) not in names:
                errs.append(f"module: broken link [`{m.group(1)}`]")
    return errs


def doc_main(argv, make_interp, out, err):
    """moxie doc FILE [-o DIR] [--format md|html] [--private] [--check]"""
    import os
    path, outdir, fmt, private, check = None, None, "html", False, False
    private = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "-o":
            outdir = argv[i + 1]
            i += 1
        elif a == "--format":
            fmt = argv[i + 1]
            i += 1
        elif a == "--private":
            private = True
        elif a == "--check":
            check = True
        else:
            path = a
        i += 1
    if not path or fmt not in ("md", "html"):
        err.write("usage: moxie doc FILE [-o DIR] [--format md|html] [--private] [--check]\n")
        return 2
    src = open(path, encoding="utf-8").read()
    try:
        clean, module_doc, items = collect(src)
    except Exception as e:      # syntax errors
        err.write(f"{path}: {e}\n")
        return 2
    if not private and any(it.exported for it in items):
        shown = [it for it in items if it.exported]
    else:
        shown = items
    results = run_doctests(clean, shown, make_interp)
    bad = [r for r in results if not r[3]]
    for it, e, x, ok, msg in bad:
        err.write(f"{path}: example failed in {it.name}: > {e}  (expected {x!r}) {msg}\n")
    title = os.path.basename(path)
    page = (render_html if fmt == "html" else render_md)(title, module_doc, shown, results)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        dest = os.path.join(outdir, "index." + fmt)
        open(dest, "w", encoding="utf-8").write(page)
        out.write(f"wrote {dest}: {len(shown)} items, {len(results)} examples, {len(bad)} failed\n")
    elif not check:
        out.write(page + "\n")
    if check:
        errs = check_links(shown, module_doc)
        for e in errs:
            err.write(f"{path}: {e}\n")
        for it in shown:
            if it.exported and not any(l.strip() for l in it.doc):
                err.write(f"{path}: warning: {it.kind} {it.name} has no doc comment\n")
        out.write(f"{len(results) - len(bad)} examples ok, {len(bad)} failed, {len(errs)} broken links\n")
        return 1 if bad or errs else 0
    return 1 if bad else 0
