"""A stress battery for the checker: programs that must be rejected (with the reason named), and look-alikes that must be accepted.
Cases live in tests/battery/*.txt, written as

    ### name
    reject: text the message must contain      (or  ok  /  ok: text the output must contain  /  reject-any)
    <source lines>

Run: python3 tests/run_battery.py [-v] [file-stem ...]"""
import glob, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
args = [a for a in sys.argv[1:] if not a.startswith("-")]
verbose = "-v" in sys.argv

def load():
    cases = []
    for path in sorted(glob.glob(os.path.join(ROOT, "tests", "battery", "*.txt"))):
        stem = os.path.basename(path)[:-4]
        if args and stem not in args:
            continue
        cur = None
        for line in open(path).read().split("\n"):
            if line.startswith("### "):
                cur = [stem, line[4:].strip(), None, []]
                cases.append(cur)
            elif cur is not None and cur[2] is None and re.match(r"(reject|ok)", line):
                cur[2] = line.strip()
            elif cur is not None:
                cur[3].append(line)
    return cases

def run(case):
    stem, name, expect, body = case
    src = "\n".join(body).strip("\n") + "\n"
    gcs = (False, True)
    if src.startswith("#gc"):
        gcs = (True,)
    results = []
    for gc in gcs:
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        want_run = expect.startswith("ok")
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run" if want_run and ":" in expect else "check", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
        os.unlink(f.name)
        o = (r.stdout + r.stderr)
        results.append((gc, r.returncode, o))
    return case, results

def judge(case, results):
    stem, name, expect, body = case
    bad = []
    for gc, rc, o in results:
        tag = " (gc)" if gc else ""
        if expect.startswith("reject"):
            want = expect.split(":", 1)[1].strip() if ":" in expect else None
            if rc == 0:
                bad.append(f"ACCEPTED{tag}: should be rejected")
            elif "syntax error" in o and "syntax" not in (want or ""):
                bad.append(f"SYNTAX{tag}: {o.strip()[:160]}")
            elif want and want not in o:
                bad.append(f"WRONG-REASON{tag}: wanted {want!r}, got {o.strip()[:200]!r}")
        else:
            want = expect.split(":", 1)[1].strip() if ":" in expect else None
            if rc != 0:
                bad.append(f"REJECTED{tag}: {o.strip()[:220]}")
            elif want and want not in o:
                bad.append(f"OUTPUT{tag}: wanted {want!r}, got {o.strip()[:120]!r}")
    return bad

cases = load()
with ThreadPoolExecutor(8) as ex:
    done = list(ex.map(run, cases))
fails = 0
for case, results in done:
    bad = judge(case, results)
    if bad:
        fails += 1
        print(f"FAIL  [{case[0]}] {case[1]}")
        for b in bad:
            print("      " + b)
    elif verbose:
        print(f"ok    [{case[0]}] {case[1]}")
print(f"{len(cases) - fails} of {len(cases)} battery cases passed" if fails else f"all {len(cases)} battery cases passed")
sys.exit(1 if fails else 0)
