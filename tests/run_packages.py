"""Packages of several files, `internal` hidden from importers, and moxie doc for a file, a package, and a program.
Run: python3 tests/run_packages.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []

def sh(d, *args):
    env = dict(os.environ, PYTHONPATH=ROOT)
    r = subprocess.run([sys.executable, "-m", "moxie", *args], cwd=d, env=env, capture_output=True, timeout=90)
    return r.returncode, r.stdout.decode() + r.stderr.decode()

def chk(name, d, args, rc_want, *wants, absent=()):
    rc, out = sh(d, *args)
    ok = rc == rc_want and all(w in out for w in wants) and not any(a in out for a in absent)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {out[:400]!r}"))
    if not ok: fails.append(name)

def make(files):
    d = tempfile.mkdtemp(prefix="mxpkg")
    for path, text in files.items():
        full = os.path.join(d, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w").write(text)
    return d

D = make({
    "util.mxi": '//! Small helpers.\n\n/// The greeting.\nexport fn greeting() String:\n  "hello"\n\ninternal retry_limit = 3\n',
    "shapes/Moxie.toml": 'name = "shapes"\nfiles = ["base.mxi", "area.mxi"]\n',
    "shapes/base.mxi": '//! Shapes with areas.\ninternal pi_ish = 3\n\n/// A square.\nexport tuple Square:\n  side: Int\n',
    "shapes/area.mxi": '/// Area of a square. See [`shapes.Square`].\n///\n/// > area(Square(side: 3))\n/// 9\nexport pure fn area(s: Square) Int:\n  s.side * s.side + pi_ish - 3\n',
    "app.mxi": 'import shapes\nimport util\nprintln(shapes.area(shapes.Square(side: 4)))\nprintln(util.greeting())\n',
    "bad.mxi": 'import util\nprintln(util.retry_limit)\n',
    "bad2.mxi": 'import util (retry_limit)\nprintln(retry_limit)\n',
    "alias.mxi": 'import util as u\nprintln(u.retry_limit)\n',
    "rebound.mxi": 'import util\nx = util\nprintln(x.retry_limit)\n',
    "main.mxi": 'println("main")\n',
    "kinds.mxi": 'internal tuple Secret:\n  n: Int\ntuple Local:\n  n: Int\nexport tuple Pub:\n  n: Int\n',
    "usetypes.mxi": 'import kinds\nfn f(s: kinds.Secret) Int:\n  s.n\nfn g(l: kinds.Local) Int:\n  l.n\nfn h(p: kinds.Pub) Int:\n  p.n\n',
    "broken/Moxie.toml": 'files = ["one.mxi", "gone.mxi"]\n',
    "broken/one.mxi": 'export fn f() Int:\n  1\n',
    "usebroken.mxi": 'import broken\nprintln(broken.f())\n',
    "local/local.mxi": 'export fn one() Int:\n  1\n',
    "uselocal.mxi": 'import local\nprintln(local.one())\n',
})

chk("files of a package share names in manifest order", D, ["run", "app.mxi"], 0, "16\nhello")
chk("a package folder with one file still loads", D, ["run", "uselocal.mxi"], 0, "1")
chk("internal is hidden from importers at check time", D, ["check", "bad.mxi"], 1, "'retry_limit' is internal to package util")
chk("and in a name list", D, ["check", "bad2.mxi"], 1, "is internal to package util")
chk("through an alias", D, ["check", "alias.mxi"], 1, "'retry_limit' is internal to package util")
chk("a rebound package is caught at run time", D, ["run", "rebound.mxi"], 1, "is internal to package util")
chk("and at run time", D, ["run", "bad.mxi", "--no-check"], 1, "is internal to package util")
chk("a listed file that is missing is an error", D, ["run", "usebroken.mxi"], 1, "gone.mxi")

chk("an internal type name is an error", D, ["check", "usetypes.mxi"], 1, "'Secret' is internal to package kinds")
chk("a file-local type name is an error", D, ["check", "usetypes.mxi"], 1, "'Local' in package kinds is not exported")
chk("an exported type name is fine", D, ["check", "usetypes.mxi"], 1, absent=("'Pub'",))

chk("doc for one file", D, ["doc", "util.mxi"], 0, "greeting", "Small helpers")
V = make({"v.mxi": '/// How long to wait.\n///\n/// > wait\n/// 5\nexport wait: Int = 5\n\ninternal knob = 1\n\nscratch = 2\n'})
chk("doc lists an exported binding, with its examples", V, ["doc", "v.mxi", "--check"], 0, "1 examples ok, 0 failed")
chk("the binding appears as a value", V, ["doc", "v.mxi"], 0, "value", "wait: Int = 5", absent=("scratch", "knob"))
chk("--private adds internal bindings but not plain ones without a comment", V, ["doc", "v.mxi", "--private"], 0, "knob", absent=("scratch",))
chk("doc links a [`name`] to its item (html)", D, ["doc", "shapes", "-o", "out_html"], 0, "wrote")
rc, out = sh(D, "doc", "shapes", "--format", "md", "-o", "out_md")
page = open(os.path.join(D, "out_md", "index.md")).read()
ok = "[`shapes.Square`](#tuple-square)" in page
print(("ok    " if ok else "FAIL  ") + "doc links a qualified name in Markdown" + ("" if ok else f"  {page[:300]!r}"))
if not ok: fails.append("md links")
page = open(os.path.join(D, "out_html", "index.html")).read()
ok = '<a href="#Square"><code>shapes.Square</code></a>' in page
print(("ok    " if ok else "FAIL  ") + "doc links a qualified name in HTML" + ("" if ok else f"  {page[-300:]!r}"))
if not ok: fails.append("html links")
chk("doc for a package covers all its files", D, ["doc", "shapes"], 0, "Square", "area", "Shapes with areas")
chk("doc for a package runs its examples across files", D, ["doc", "shapes", "--check"], 0, "1 examples ok, 0 failed, 0 broken links")
chk("doc --all adds the imported packages", D, ["doc", "app.mxi", "--all"], 0, "shapes", "util", "greeting", "Square")
chk("without --all only the file", D, ["doc", "app.mxi"], 0, absent=("greeting",))
chk("doc of an unknown name", D, ["doc", "nothing"], 2, "cannot find a file or package named 'nothing'")
chk("doc with no name uses main.mxi", D, ["doc"], 0, "main.mxi")
out = os.path.join(D, "site")
chk("doc --all -o writes an index and a page per package", D, ["doc", "app.mxi", "--all", "-o", out], 0, "wrote", "3 pages")
ok = all(os.path.isfile(os.path.join(out, f)) for f in ("index.html", "shapes.html", "util.html", "app.mxi.html"))
print(("ok    " if ok else "FAIL  ") + "the pages exist")
if not ok: fails.append("the pages exist")
chk("a broken qualified link is reported by --check", make({"p/Moxie.toml": 'files = ["a.mxi"]\n', "p/a.mxi": '/// See [`q.nothing`].\nexport fn f() Int:\n  1\n'}), ["doc", "p", "--check"], 1, "broken link")
chk("--std adds the packages that ship with moxie", D, ["--gc", "doc", "app.mxi", "--all", "--std"], 0, "shapes")

# local (private) impls of a foreign interface for a foreign type
SQ = 'export tuple Square:\n  side: Int\n'
SP = 'export interface Speaker:\n  fn say(self) String\n'
IMPL = 'impl talk.Speaker for shapes.Square:\n  fn say(self) String:\n    "side ${self.side}"\n'
HEAD = 'import shapes\nimport talk\n'
O = make({
    "shapes.mxi": SQ, "talk.mxi": SP,
    "ok.mxi": HEAD + IMPL + 'println(shapes.Square(side: 4).say())\n',
    "twice.mxi": HEAD + IMPL + IMPL,
    "mid.mxi": HEAD + 'export fn mk() shapes.Square:\n  shapes.Square(side: 2)\n' + IMPL + 'export fn inside() String:\n  mk().say()\n',
    "mid2.mxi": HEAD + 'export fn inside2() String:\n  shapes.Square(side: 3).say()\n' + IMPL.replace('"side ${self.side}"', '"other ${self.side}"'),
    "viaimport.mxi": 'import mid\nprintln(mid.mk().say())\n',
    "inside.mxi": 'import mid\nprintln(mid.inside())\n',
    "both.mxi": 'import mid\nimport mid2\nprintln(mid.inside())\nprintln(mid2.inside2())\n',
    "owned.mxi": 'import talk\ntuple Sq:\n  side: Int\nimpl talk.Speaker for Sq:\n  fn say(self) String:\n    "mine"\nprintln(Sq(side: 1).say())\n',
   })
chk("a local impl of a foreign interface for a foreign type works in its own package", O, ["ok.mxi"], 0, "side 4")
chk("a second local impl of the same pair is an error", O, ["twice.mxi"], 2, "already implements")
chk("a package can use its own local impl", O, ["inside.mxi"], 0, "side 2")
chk("an importer does not see another package's local impl", O, ["viaimport.mxi"], 1, "no method or function 'say'", absent=("side 2",))
chk("two packages can each have their own local impl of the same pair", O, ["both.mxi"], 0, "side 2", "other 3")
chk("an impl for your own type still works", O, ["owned.mxi"], 0, "mine")

print()
print("FAILURES: " + ", ".join(fails) if fails else "all package tests passed")
sys.exit(1 if fails else 0)
