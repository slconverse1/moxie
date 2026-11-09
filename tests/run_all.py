"""Run every tests/run_*.py and report each file that fails (nonzero exit, a FAIL line, a Traceback, or "N failed").
Run: python3 tests/run_all.py [-j N] [pattern]   (exit 1 if anything failed; -j runs files in parallel, which can make the timing-sensitive
cteval tests time out, so the default is one at a time)"""
import glob, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
args = sys.argv[1:]
jobs = 1
if "-j" in args:
    i = args.index("-j"); jobs = int(args[i + 1]); del args[i:i + 2]
pat = args[0] if args else ""
files = sorted(f for f in glob.glob(os.path.join(HERE, "run_*.py")) if os.path.basename(f) != "run_all.py" and pat in f)

def one(f):
    try:
        r = subprocess.run([sys.executable, f], cwd=ROOT, capture_output=True, timeout=900)
        out, rc = (r.stdout + r.stderr).decode(errors="replace"), r.returncode
    except subprocess.TimeoutExpired:
        out, rc = "timeout", 124
    bad = [l for l in out.splitlines() if l.startswith("FAIL") or "Traceback" in l or "CRASH" in l or re.search(r"\b[1-9]\d* failed", l)]
    gc = re.findall(r"'err': ([1-9]\d*)", out)
    tail = out.strip().splitlines()[-12:] if (rc != 0 or bad or gc) else []
    return f, rc, bad + [f"guide err {g}" for g in gc], tail

failed = []
with ThreadPoolExecutor(jobs) as ex:
    for f, rc, bad, tail in ex.map(one, files):
        name = os.path.basename(f)
        if rc != 0 or bad:
            failed.append(name)
            print(f"FAIL  {name} (exit {rc})")
            for l in bad[:6]:
                print("      " + l[:200])
            print("      -- last lines of its output:")
            for l in tail:
                print("      | " + l[:200])
        else:
            print(f"ok    {name}")
print(f"\n{len(files) - len(failed)} of {len(files)} files passed" + ("" if not failed else "; failed: " + ", ".join(failed)))
sys.exit(1 if failed else 0)
