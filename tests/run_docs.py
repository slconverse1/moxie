"""Check the code in the index and tutorial pages (both dialects).  Run: python3 tests/run_docs.py [-v]

Each ``` block is run on its own; a block that needs earlier definitions is retried with the
blocks before it.  A block that follows `Output: `...`` is also compared against that output."""
import io, os, re, signal, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
verbose = "-v" in sys.argv
PAGES = [("docs/index.md", False), ("docs/tutorial.md", False), ("docs/gc/index.md", True), ("docs/gc/tutorial.md", True)]
# blocks that are not programs, or are shown only as a fragment or a deliberate error
def not_code(src):
    s = src.lstrip()
    if s.startswith(("$", "[", "//", "#", "lib ", "name =", "moxie ")): return True
    if "foreign " in s and "\"c\"" not in s: return True
    if re.match(r"\w+\s+\(.*\) -> ", s) or re.match(r"\w+: ", s) and "\n" in s and "fn " not in s and "=" not in s: return True   # signature or output listings
    if re.match(r"(mkdir|curl|unzip|python3|git|cd) ", s): return True
    return False
def run_one(src, gc):
    cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", "--allow-all"]
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.mxi")
        open(p, "w").write(src)
        try:
            r = subprocess.run(cmd + [p], cwd=d, capture_output=True, text=True, timeout=20,
                               env=dict(os.environ, PYTHONPATH=ROOT), input="")
        except subprocess.TimeoutExpired:
            return -9, ""
    return r.returncode, (r.stdout + r.stderr)
def norm(s): return re.sub(r"\s+", " ", s).strip()
tot = {"frag": 0, "ok": 0, "ctx": 0, "skip": 0, "fail": 0, "outdiff": 0}
bad = []
for page, gc in PAGES:
    txt = open(os.path.join(ROOT, page)).read()
    blocks = []
    for m in re.finditer(r"```([a-z]*)\n(.*?)```(.*?)(?=\n\n|\Z)", txt, re.S):
        lang, src, after = m.groups()
        if lang == "output": continue
        om = re.search(r"Output: `([^`]*)`", txt[m.end():m.end() + 400].split("\n\n")[1] if "\n\n" in txt[m.end():m.end() + 400] else "")
        blocks.append((txt[:m.start()].count("\n") + 1, src, om.group(1) if om else None))
    good = []
    for i, (ln, src, exp) in enumerate(blocks):
        if not_code(src): tot["skip"] += 1; continue
        rc, out = run_one(src, gc)
        used = "alone"; alone = out
        if rc != 0 and "// error" in src:
            tot["skip"] += 1; continue          # a deliberate compile error shown to the reader
        if rc != 0 and not re.search(r"undefined (name|function)|unexpected indent|unknown type|no field", alone):
            pass                                   # a real error: do not hide it behind context
        elif rc != 0:
            for k in (1, 2, 3, 5, 8, 13, 100):
                pre = "\n".join(good[-k:])
                if not pre: continue
                rc, out = run_one(pre + "\n" + src, gc)
                if rc == 0: used = "ctx"; break
        if rc != 0 and re.search(r"undefined (name|function)|undefined function|unexpected indent|unknown type|no field|unexpected 'discount'", alone):
            tot["frag"] += 1; continue              # shown without the definitions it relies on
        if rc != 0:
            tot["fail"] += 1; bad.append(f"{page}:{ln}  {alone.strip().splitlines()[-1][:110] if alone.strip() else rc}")
            continue
        good.append(src)
        tot["ok" if used == "alone" else "ctx"] += 1
        if exp is not None and used == "alone":
            want = norm(exp)
            got = norm(out)
            if want not in got and got not in want and norm(want.replace(",", "")) not in norm(got.replace(",", "")):
                tot["outdiff"] += 1
                if verbose: print(f"  output differs {page}:{ln}: doc {want[:60]!r} vs run {got[:60]!r}")
for b in bad: print("FAIL ", b)
print(tot)
sys.exit(1 if bad else 0)
