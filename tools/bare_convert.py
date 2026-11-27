"""Rewrite each multi-line bracketed call (name( ... ) over several lines) as the bare form: the name alone on its
line, its arguments indented under it, one per line.  Declarations keep their brackets.  Returns (text, skipped)
where skipped lists the line numbers of openers it could not rewrite safely."""
import re, sys
sys.path.insert(0, "/tmp/ffb")
from moxie import lexer as L
L._check_strict_groups = lambda out, file: None        # the converter reads sources that the new check rejects
DECL = re.compile(r"\b(fn|pattern|interface|impl|foreign|test|type|enum|tuple|property|fiber|pure|impure|parks|prints|export|internal|union|opaque|forward|scope|with|where|if|elif|while|for|when|match|return|else)\b")

def _pairs(out):
    stack, close = [], {}
    for i, t in enumerate(out):
        if t.kind == "OP" and t.val in ("(", "[", "{"):
            stack.append(i)
        elif t.kind == "OP" and t.val in (")", "]", "}") and stack:
            close[stack.pop()] = i
    return close

def _commas_top(text):
    depth = 0; q = False
    for ch in text:
        if ch == '"': q = not q
        if q: continue
        if ch in "([{": depth += 1
        elif ch in ")]}": depth -= 1
        elif ch == "," and depth == 0: return True
    return False

def convert(src):
    skipped = []
    skipped_at = set()
    for _ in range(2000):
        lines = src.split("\n")
        try:
            out = L.Lexer(src + "\n", "x.mxi").tokenize()
        except Exception as e:
            return src, skipped + [("lex", str(e)[:120])]
        close = _pairs(out)
        cand = None
        for i, t in enumerate(out):
            if not (t.kind == "OP" and t.val == "(") or i == 0:
                continue
            p = out[i - 1]
            if not (p.kind == "NAME" or (p.kind == "OP" and p.val in ("]", ")"))) or t.sp:
                continue
            c = close.get(i)
            if c is None or out[c].line == t.line:
                continue
            ln = lines[t.line - 1]
            if DECL.search(ln) or (t.line, t.col) in skipped_at:
                continue
            cand = (i, c); break
        if cand is None:
            break
        i, c = cand
        o, cl = out[i].line, out[c].line
        ln = lines[o - 1]
        ind = len(ln) - len(ln.lstrip(" "))
        name_line = ln[:out[i].col - 1]
        if name_line.strip() == "" or not re.search(r"[A-Za-z_0-9\])]$", name_line):
            skipped.append((o, "no name before ("))
            continue
        closing = lines[cl - 1]
        before = closing[:out[c].col - 1]
        after = closing[out[c].col:]
        if after.strip() != "":
            skipped.append((o, "text after the closing bracket")); skipped_at.add((o, out[i].col))
            continue
        rest = ln[out[i].col:]
        items = []
        if rest.strip() != "":
            items.append(" " * ind + rest.strip())      # text after the opener is the first argument
        items += lines[o:cl - 1] + ([before] if before.strip() != "" else [])
        if any(_commas_top(x) for x in items):
            skipped.append((o, "a comma between items on one line")); skipped_at.add((o, out[i].col))
            continue
        items = [x for x in items if x.strip() != ""]
        if not items:
            new = [name_line.rstrip() + "()"]
        else:
            first = len(items[0]) - len(items[0].lstrip(" "))
            delta = (ind + 2) - first
            new = [name_line.rstrip()]
            for x in items:
                k = len(x) - len(x.lstrip(" "))
                new.append(" " * max(0, k + delta) + x.lstrip(" "))
        lines[o - 1:cl] = new
        src = "\n".join(lines)
    return src, skipped

if __name__ == "__main__":
    s = open(sys.argv[1], encoding="utf-8").read()
    t, sk = convert(s)
    sys.stdout.write(t)
    print("skipped:", sk, file=sys.stderr)
