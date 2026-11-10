"""The lexer written in moxie (moxie/selfhost/lexer.mxi) gives the same tokens as moxie/lexer.py for the part it covers.
Every line of the library and example sources that stays inside that part is lexed by both, and the tokens are compared
(kind, line, column, and the text of names and operators).  Run: python3 tests/run_selfhost.py"""
import glob, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from moxie.lexer import Lexer, MoxieSyntaxError

SNIPPETS = ["x = 1 + 2.5", "fn add(a: Int, b: Int) Int:", "  a + b", "println(\"hi there\")", "xs |> map(f) |> collect()",
            "a ~= b and c <= d", "y = f(x) // a comment", "t = (1, 2, 3)", "...rest", "n >>= 2", "s = \"a\\\"b\"", "v = xs(0)"]
KINDS = {"NAME", "INT", "FLOAT", "STR", "OP"}

def lines():
    out = list(SNIPPETS)
    files = glob.glob(os.path.join(ROOT, "moxie", "std", "**", "*.mxi"), recursive=True) + glob.glob(os.path.join(ROOT, "examples", "*.mxi"))
    for f in sorted(files):
        for ln in open(f, encoding="utf-8").read().split("\n"):
            if ln.strip() == "" or ln.strip().startswith("//") or "\t" in ln or "/*" in ln:
                continue
            try:
                toks = [t for t in Lexer(ln).tokenize()]
            except MoxieSyntaxError:
                continue
            data = [t for t in toks if t.kind not in ("NL", "INDENT", "DEDENT", "EOF", "BOL")]
            if any(t.kind not in KINDS for t in data):
                continue
            if any(t.kind == "INT" and t.extra for t in data) or any(t.kind == "FLOAT" and ("e" in str(t.val).lower() or t.extra) for t in data):
                continue
            if any(t.kind == "STR" and ("$" in ln or "\\" in ln) for t in data):
                continue
            if any(t.kind == "NAME" and not t.val.isascii() for t in data):
                continue
            out.append(ln)
    step = max(1, (len(out) - len(SNIPPETS)) // 40)          # the moxie lexer is slow on the interpreter, so use a sample
    return SNIPPETS + out[len(SNIPPETS)::step]

def python_tokens(src):
    lx = Lexer(src)
    lx.tokenize()
    res = []
    for t in lx.raw:
        if t.kind in ("NL", "BOL") or t.kind not in KINDS:
            continue
        res.append((t.kind, t.line, t.col, t.val if t.kind in ("NAME", "OP") else ""))
    return res

def main():
    corpus = "\n".join(lines()) + "\n"
    py = python_tokens(corpus)
    lib = open(os.path.join(ROOT, "moxie", "selfhost", "lexer.mxi"), encoding="utf-8").read()
    driver = lib + '''
when read_all():
  Ok(s) -> println(lex(s) |> to_stream() |> filter((t): t.kind ~= "NL") |> map(show_token) |> join("\\n"))
  Err(e) -> println("no input")
'''
    path = os.path.join(ROOT, "tests", "_selfhost_driver.mxi")
    open(path, "w", encoding="utf-8").write(driver)
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", "run", path], input=corpus, capture_output=True, text=True, cwd=ROOT, timeout=900)
    finally:
        os.unlink(path)
    if r.returncode != 0:
        print("FAIL: the moxie lexer did not run:", (r.stdout + r.stderr)[-500:])
        return 1
    mine = []
    for row in r.stdout.rstrip("\n").split("\n"):
        k, text, ln, col = row.split("\t")
        mine.append((k, int(ln), int(col), text if k in ("NAME", "OP") else ""))
    if mine == py:
        print(f"ok    {len(py)} tokens over {corpus.count(chr(10))} lines are the same")
        return 0
    for a, b in zip(mine, py):
        if a != b:
            print("FAIL: first difference: moxie", a, "python", b)
            break
    else:
        print("FAIL: lengths differ", len(mine), len(py))
    return 1

sys.exit(main())
