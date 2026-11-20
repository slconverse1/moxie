"""String patterns with holes: `"--port=${p Int}"`, `"${stem}.mxi"`.  Run: python3 tests/run_strpat.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPT = 'fn option(arg String) String\n  when arg\n    "--port=${p Int}" -> "port ${p + 1}"\n    "--${name}" -> "flag ${name}"\n    _ -> "other"\n'
CASES = [
    ("typed hole and prefix", OPT + 'println(option("--port=80"))\nprintln(option("--port=x"))\nprintln(option("--v"))\nprintln(option("go"))\n', 0, "port 81\nflag port=x\nflag v\nother"),
    ("suffix and alternatives", 'fn k(f String) String\n  when f\n    "${s}.mxi" -> "src ${s}"\n    "${s}.md" | "${s}.txt" -> "text ${s}"\n    _ -> "?"\nprintln(k("a.mxi"))\nprintln(k("n.txt"))\nprintln(k("a.mxi.mxi"))\nprintln(k("z"))\n', 0, "src a\ntext n\nsrc a.mxi\n?"),
    ("both ends", 'fn r(p String) String\n  when p\n    "/api/${n}.json" -> "json ${n}"\n    "/api/${rest}" -> "api ${rest}"\n    "/" -> "home"\n    _ -> "404"\nprintln(r("/api/u.json"))\nprintln(r("/api/u"))\nprintln(r("/"))\nprintln(r("/x"))\n', 0, "json u\napi u\nhome\n404"),
    ("two holes split at the first literal", 'fn kv(s String) String\n  when s\n    "${k}=${v}" -> "$k -> $v"\n    _ -> "no"\nprintln(kv("a=b=c"))\nprintln(kv("ab"))\n', 0, "a -> b=c\nno"),
    ("is test", 'if "k=3" is "k=${v Int}" then println("yes")\nprintln("k=x" is "k=${v Int}")\n', 0, "yes\nfalse"),
    ("hole types", 'fn f(s String) String\n  when s\n    "d=${x Double}" -> "double"\n    "b=${x Bool}" -> "bool"\n    _ -> "-"\nprintln(f("d=1.5"))\nprintln(f("b=true"))\nprintln(f("b=maybe"))\n', 0, "double\nbool\n-"),
    ("ignored hole", 'fn f(s String) Bool\n  when s\n    "a${_}z" -> true\n    _ -> false\nprintln(f("abcz"))\nprintln(f("abc"))\n', 0, "true\nfalse"),
    ("empty hole text", 'fn f(s String) String\n  when s\n    "${x}!" -> "[${x}]"\n    _ -> "-"\nprintln(f("!"))\n', 0, "[]"),
    ("typed hole is typed", 'fn f(s String) String\n  when s\n    "n=${n Int}" -> n + "a"\n    _ -> "x"\nprintln(f("n=1"))\n', 1, "cannot apply `+`"),
    ("pattern on a non-string", 'fn f(n Int) String\n  when n\n    "a${x}" -> x\n    _ -> "x"\nprintln(f(1))\n', 1, "string pattern"),
    ("adjacent holes", 'fn f(s String) String\n  when s\n    "${a}${b}" -> a\n    _ -> "x"\nprintln(f("ab"))\n', 1, "need literal text between them"),
    ("a name twice", 'fn f(s String) String\n  when s\n    "${a}-${a}" -> a\n    _ -> "x"\nprintln(f("a-b"))\n', 1, "bound twice"),
    ("bad hole type", 'fn f(s String) String\n  when s\n    "n=${n Foo}" -> "x"\n    _ -> "x"\nprintln(f("n=1"))\n', 1, "can be typed"),
    ("needs a catch-all", 'fn f(s String) String\n  when s\n    "a${x}" -> x\nprintln(f("ab"))\n', 1, "needs a `_` arm"),
    ("alternatives bind the same names", 'fn g(s String) String\n  when s\n    "${a}.md" | "${b}.txt" -> "x"\n    _ -> "y"\nprintln(g("a.md"))\n', 1, "same names"),
]
bad = 0
for name, src, want_rc, want in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    for flags in ([], ["--gc"]):
        r = subprocess.run([sys.executable, "-m", "moxie"] + flags + ["run", f.name], cwd=ROOT, capture_output=True, timeout=60)
        out = (r.stdout + r.stderr).decode()
        ok = (r.returncode == 0) == (want_rc == 0) and want in out
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if flags else "") + ("" if ok else "  " + repr(out[-200:])))
        bad += not ok
    os.unlink(f.name)
print(f"{bad} failed")
sys.exit(1 if bad else 0)
