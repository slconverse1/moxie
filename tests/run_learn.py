"""Runs every example of the teaching guide (lessons/*.md) in both dialects and compares the output.  Run: python3 tests/run_learn.py [lesson-prefix ...] [-v]

An example is a ```moxie block.  If a ```output block follows it, the program's whole standard output must equal it; if an ```error block
follows it, the program must fail and its message must contain the text; with neither, the program must run and print nothing.
```moxie-nocheck blocks are skipped.  A block may carry `//! stdin: text` lines to feed its input, and `//! command: test` (or `check`) to run that command instead of `run`."""
import os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_learn

def dialect_blocks(txt, gc):
    t = make_learn.dialect_text(txt, gc)
    lines, out, i, files = t.split("\n"), [], 0, {}
    while i < len(lines):
        if lines[i].strip() == "```moxie":
            j = i + 1
            while lines[j].strip() != "```":
                j += 1
            src = "\n".join(lines[i + 1:j]) + "\n"
            k = j + 1
            while k < len(lines) and lines[k].strip() == "":
                k += 1
            kind, want = None, None
            if k < len(lines) and lines[k].strip() in ("```output", "```error"):
                kind = lines[k].strip()[3:]
                e = k + 1
                while lines[e].strip() != "```":
                    e += 1
                want = "\n".join(lines[k + 1:e])
                j = e
            m = re.match(r"//! file: (\S+)\n", src)
            if m:                                     # a supporting file: it belongs to the next program
                files[m.group(1)] = src[m.end():]
            else:
                out.append((i + 1, src, kind, want, dict(files)))
                files.clear()
            i = j + 1
        else:
            i += 1
    return out

def run(job):
    name, line, src, kind, want, gc, files = job
    stdin = "\n".join(re.findall(r"^//! stdin: ?(.*)$", src, re.M))
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "main.mxi")
        for fname, ftext in files.items():
            os.makedirs(os.path.dirname(os.path.join(d, fname)) or d, exist_ok=True)
            open(os.path.join(d, fname), "w").write(ftext)
        verb = (re.findall(r"^//! command: (\w+)", src, re.M) or ["run"])[0]
        open(p, "w").write(re.sub(r"^//! .*\n", "", src, flags=re.M))      # what the reader sees is what runs, line numbers included
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + [verb, p]
        try:
            r = subprocess.run(cmd, cwd=ROOT, input=stdin + ("\n" if stdin else ""), capture_output=True, text=True, timeout=60)
            rc, out, err = r.returncode, r.stdout, r.stderr
        except subprocess.TimeoutExpired:
            rc, out, err = -1, "", "timeout"
    if kind == "error":
        good = rc != 0 and want.strip() in (out + err)
    elif kind == "output":
        good = (rc == 0 or verb == "test") and out.rstrip("\n") == want.rstrip("\n")
    else:
        good = rc == 0 and out.strip() == ""
    why = "" if good else f"  -> rc={rc} out={out.strip()[:300]!r} err={err.strip()[:300]!r} want={want!r}"
    return good, f"{name}:{line}{' (gc)' if gc else ''}{why}"

def fill(args):
    """--fill: an empty ```output block gets the program's actual output (read it before you keep it)."""
    for _, ls in make_learn.lessons():
        for slug, _, txt in ls:
            if args and not any(slug.startswith(a) for a in args):
                continue
            lines, i, changed, ingc, sup = txt.split("\n"), 0, False, False, {}
            while i < len(lines):
                if lines[i].strip() in ("@gc", "@nogc", "@end"):
                    ingc = lines[i].strip() == "@gc"
                if lines[i].strip() == "```moxie":
                    j = i + 1
                    while lines[j].strip() != "```":
                        j += 1
                    k = j + 1
                    while k < len(lines) and lines[k].strip() == "":
                        k += 1
                    src = "\n".join(lines[i + 1:j]) + "\n"
                    if src.startswith("//! file: "):
                        sup[re.match(r"//! file: (\S+)\n", src).group(1)] = src[src.index("\n") + 1:]
                    elif k + 1 < len(lines) and lines[k].strip() in ("```output", "```error") and lines[k + 1].strip() == "```":
                        with tempfile.TemporaryDirectory() as d:
                            p = os.path.join(d, "main.mxi")
                            for fname, ftext in sup.items():
                                os.makedirs(os.path.dirname(os.path.join(d, fname)) or d, exist_ok=True)
                                open(os.path.join(d, fname), "w").write(ftext)
                            open(p, "w").write(re.sub(r"^//! .*\n", "", src, flags=re.M))
                            stdin = "\n".join(re.findall(r"^//! stdin: ?(.*)$", src, re.M))
                            verb = (re.findall(r"^//! command: (\w+)", src, re.M) or ["run"])[0]
                            r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if ingc else []) + [verb, p], cwd=ROOT, input=stdin + "\n", capture_output=True, text=True, timeout=60)
                        got = r.stdout.rstrip("\n") if lines[k].strip() == "```output" else re.sub(r"^main\.mxi:\d+(:\d+)?: ", "", r.stderr.strip(), flags=re.M)
                        lines[k + 1:k + 1] = got.split("\n")
                        changed = True
                    if not src.startswith("//! file: "):
                        sup.clear()
                    i = j + 1
                else:
                    i += 1
            if changed:
                open(os.path.join(make_learn.SRC, slug + ".md"), "w", encoding="utf-8").write("\n".join(lines))
                print("filled", slug)

if __name__ == "__main__":
    if "--fill" in sys.argv:
        fill([a for a in sys.argv[1:] if not a.startswith("-")])
        sys.exit(0)
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    jobs = []
    for _, ls in make_learn.lessons():
        for slug, _, txt in ls:
            if args and not any(slug.startswith(a) for a in args):
                continue
            for gc in (False, True):
                for line, src, kind, want, files in dialect_blocks(txt, gc):
                    jobs.append((slug, line, src, kind, want, gc, files))
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(run, jobs))
    bad = [m for g, m in res if not g]
    for m in bad:
        print("FAIL  " + m)
    if "-v" in sys.argv:
        for g, m in res:
            if g:
                print("ok    " + m)
    print(f"{len(res) - len(bad)} of {len(res)} examples passed")
    sys.exit(1 if bad else 0)
