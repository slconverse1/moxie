"""The [native] manifest section.  Run: python3 tests/run_native.py"""
import os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []


def project(files):
    d = tempfile.mkdtemp()
    for name, text in files.items():
        p = os.path.join(d, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(text)
    return d


def chk(name, d, rc_want, *wants, cmd="run", entry="main.mxi"):
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, os.path.join(d, entry)], cwd=ROOT, capture_output=True, text=True, timeout=60)
    out = r.stdout + r.stderr
    good = (r.returncode == rc_want or (rc_want == 2 and r.returncode != 0)) and all(w in out for w in wants)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={r.returncode} {out[:240]!r}"))
    if not good:
        fails.append(name)
    shutil.rmtree(d, ignore_errors=True)


FOREIGN = 'foreign "m"\n  pure fn cos(x Double) Double\n'
MAIN = FOREIGN + 'println(cos(0.0))\n'

chk("the error is found by check, before anything runs", project({"main.mxi": MAIN, "Moxie.toml": 'name = "t"\n'}), 2, "no [native] section", cmd="check")
chk("a script with no manifest may declare foreign functions", project({"main.mxi": MAIN}), 0, "1.0")
chk("an entry manifest with [native] may", project({"main.mxi": MAIN, "Moxie.toml": 'name = "t"\nfiles = ["main.mxi"]\n[native]\nlibs = ["m"]\n'}), 0, "1.0")
chk("an entry manifest without [native] may not", project({"main.mxi": MAIN, "Moxie.toml": 'name = "t"\nfiles = ["main.mxi"]\n'}), 2,
    "the entry package declares foreign functions", "no [native] section", 'libs = ["m"]')
chk("a library not in libs is refused", project({"main.mxi": MAIN, "Moxie.toml": 'name = "t"\n[native]\nlibs = ["z"]\n'}), 2,
    "names the native library 'm'", "not in its [native] libs (z)")
chk("[native] without libs lists nothing to check", project({"main.mxi": MAIN, "Moxie.toml": 'name = "t"\n[native]\npaths = ["lib"]\n'}), 0, "1.0")
chk("an unknown [native] key is an error", project({"main.mxi": MAIN, "Moxie.toml": 'name = "t"\n[native]\nlibraries = ["m"]\n'}), 2, "unknown key 'libraries' in [native]")
chk("libs must be a list of strings", project({"main.mxi": MAIN, "Moxie.toml": 'name = "t"\n[native]\nlibs = "m"\n'}), 2, "[native] libs must be a list of strings")

PKG = 'export fn root(x Double) Double = cos(x)\n'
USE = 'import nat\nprintln(nat.root(0.0))\n'
chk("an imported package with [native] may declare foreign functions",
    project({"main.mxi": USE, "nat/nat.mxi": FOREIGN + PKG, "nat/Moxie.toml": 'name = "nat"\nfiles = ["nat.mxi"]\n[native]\nlibs = ["m"]\n'}), 0, "1.0")
chk("an imported package whose manifest has no [native] may not",
    project({"main.mxi": USE, "nat/nat.mxi": FOREIGN + PKG, "nat/Moxie.toml": 'name = "nat"\nfiles = ["nat.mxi"]\n'}), 2,
    "package 'nat' declares foreign functions", "no [native] section")
chk("a package may only name the libraries it lists",
    project({"main.mxi": USE, "nat/nat.mxi": FOREIGN + PKG, "nat/Moxie.toml": 'name = "nat"\n[native]\nlibs = ["z"]\n'}), 2,
    "package 'nat' names the native library 'm'")
chk("a package file with no manifest is as lenient as a script", project({"main.mxi": USE, "nat.mxi": FOREIGN + PKG}), 0, "1.0")

# paths: a library found only through [native] paths
lib = subprocess.run(["bash", "-c", "command -v cc gcc | head -1"], capture_output=True, text=True).stdout.strip()
if lib:
    d = project({"main.mxi": 'foreign "tw"\n  pure fn twice(x Int32) Int32\nprintln(twice(21i32))\n',
                 "native/tw.c": "int twice(int x) { return 2 * x; }\n",
                 "Moxie.toml": 'name = "t"\n[native]\nlibs = ["tw"]\npaths = ["native"]\n'})
    subprocess.run([lib, "-shared", "-fPIC", "-o", os.path.join(d, "native", "libtw.so"), os.path.join(d, "native", "tw.c")], check=True)
    chk("paths are searched for a library", d, 0, "42")
    d = project({"main.mxi": 'foreign "tw"\n  pure fn twice(x Int32) Int32\nprintln(twice(21i32))\n',
                 "native/tw.c": "int twice(int x) { return 2 * x; }\n",
                 "Moxie.toml": 'name = "t"\n[native]\nlibs = ["tw"]\n'})
    subprocess.run([lib, "-shared", "-fPIC", "-o", os.path.join(d, "native", "libtw.so"), os.path.join(d, "native", "tw.c")], check=True)
    chk("without paths the library is not found", d, 1, "cannot load native library")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
