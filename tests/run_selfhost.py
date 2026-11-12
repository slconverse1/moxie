"""The lexer written in moxie (moxie/selfhost/lexer.mxi) gives the same tokens as moxie/lexer.py for the part it covers.
A sample of runs of consecutive lines from the library and example sources that stay inside that part is lexed by both,
and the tokens are compared: names, numbers, strings, operators, and the logical-line tokens NL, INDENT, DEDENT, and EOF
(kind, line, column, and the text of names and operators).  Run: python3 tests/run_selfhost.py"""
import glob, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from moxie.lexer import Lexer, MoxieSyntaxError

SNIPPETS = ["x = 1 + 2.5", 'fn add(a: Int, b: Int) Int', "  a + b", "println(\"hi there\")", "xs |> map(f) |> collect()",
            "a ~= b and c <= d", "n = 0xFF_FFu8 + 0b1010 + 0o17 + 1_000", "x = 1.5e-3 + 2E4 + 3.0f + 5d + 10ms + 2h", "t = 7u32 + 8i64", "c = 'a' + '\\n' + '\\'' + '\\u{41}'", "b = b\"GET /\" + b'\\x7F'", "r = r\"C:\\t\" + r#\"a\"b\"#", "x = 1 /* a\n b */ + 2", "y /* c /* nested */ d */ = 3", "// r\"not raw", "r = r + b", "y = f(x) // a comment", "t = (1, 2, 3)", "...rest", "n >>= 2", "s = \"a\\\"b\"", "v = xs(0)"]
KINDS = {"NAME", "INT", "FLOAT", "DUR", "DEC", "STR", "CHAR", "BCHAR", "BYTES", "OP"}
STRUCT = {"NL", "INDENT", "DEDENT", "EOF"}

def supported(ln):
    """True when this one line stays inside the part the moxie lexer covers."""
    if "\t" in ln:
        return False
    try:
        toks = Lexer(ln).tokenize()
    except MoxieSyntaxError:
        return False
    data = [t for t in toks if t.kind not in ("NL", "INDENT", "DEDENT", "EOF", "BOL")]
    if any(t.kind not in KINDS for t in data):
        return False
    if any(t.kind == "STR" and ("$" in ln or "\\" in ln) for t in data):
        return False
    if any(t.kind == "NAME" and not t.val.isascii() for t in data):
        return False
    return True

def runs():
    """Runs of up to 12 consecutive supported lines that begin at the left margin (blank and comment lines may sit inside)."""
    out = []
    files = glob.glob(os.path.join(ROOT, "moxie", "std", "**", "*.mxi"), recursive=True) + glob.glob(os.path.join(ROOT, "examples", "*.mxi"))
    for f in sorted(files):
        cur = []
        for ln in open(f, encoding="utf-8").read().split("\n"):
            plain = ln.strip() == "" or ln.strip().startswith("//")
            if plain and not cur:
                continue
            if (plain or supported(ln)) and len(cur) < 12 and (cur or not ln.startswith(" ")):
                cur.append(ln)
            else:
                if cur and any(x.strip() and not x.strip().startswith("//") for x in cur):
                    out.append(cur)
                cur = [ln] if (supported(ln) and not ln.startswith(" ")) else []
        if cur and any(x.strip() and not x.strip().startswith("//") for x in cur):
            out.append(cur)
    return out

def lines():
    rs = runs()
    step = max(1, len(rs) // 30)                     # the moxie lexer is slow on the interpreter, so use a sample
    text = list(SNIPPETS)
    for r in rs[::step]:
        text += r + [""]
    return text

def python_tokens(src):
    res = []
    for t in Lexer(src).tokenize():
        if t.kind not in KINDS and t.kind not in STRUCT:
            continue
        res.append((t.kind, t.line, t.col, t.val if t.kind in ("NAME", "OP") else ""))
    return res

def main():
    corpus = "\n".join(lines()) + "\n"
    py = python_tokens(corpus)
    lib = open(os.path.join(ROOT, "moxie", "selfhost", "lexer.mxi"), encoding="utf-8").read()
    driver = lib + '''
when read_all()
  Ok(s) -> println(lex_lines(s) |> to_stream() |> map(show_token) |> join("\\n"))
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
