"""The `io` package: Reader and Writer over files, stdout, stderr and an in-memory Buffer.  Run: python3 tests/run_io.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp()
P = os.path.join(TMP, "f.txt")
CASES = [
 ("write_bytes reaches stdout", 'r = write_bytes(stdout, to_utf8("hi\\n"))\nprintln(r)\n', 0, "hi\nOk(())"),
 ("say and copy through a Buffer", 'import io\nb = io.buffer_of("hello\\n")\nout = io.buffer()\nn = io.copy(ref b, ref out)?\nprintln(n)\nio.copy(ref out, ref stdout)?\n', 0, "6\nhello"),
 ("read_all", 'import io\nb = io.buffer_of("abcdef")\nxs = io.read_all(ref b)?\nprintln(len(xs))\n', 0, "6"),
 ("a Buffer reads in pieces and ends with an empty array", 'import io\nb = io.buffer_of("abc")\na = ref b.read(2)?\nc = ref b.read(2)?\nd = ref b.read(2)?\nprintln("${len(a)} ${len(c)} ${len(d)}")\n', 0, "2 1 0"),
 ("a file is a Writer and a Reader", f'import io\nf = open_file("{P}", Create)?\nio.say(ref f, "to a file\\n")?\nclose(f)\ng = open_file("{P}")?\nb = io.buffer()\nn = io.copy(ref g, ref b)?\nclose(g)\nprintln(n)\n', 0, "10"),
 ("stdout takes say", 'import io\nio.say(ref stdout, "ok\\n")?\n', 0, "ok"),
 ("a function written against Writer takes any of them", 'import io\nfn greet[W io.Writer](ref w W) Result[Unit, Error]\n  io.say(ref w, "hi\\n")\nb = io.buffer()\ngreet(ref b)?\ngreet(ref stdout)?\nprintln(len(io.contents(b)))\n', 0, "hi\n3"),
 ("a Reader call needs ref", 'import io\nb = io.buffer_of("x")\nr = b.read(1)\n', 2, "changes its receiver"),
]
fails = []
for name, src, rc, want in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name], cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = (r.stdout + r.stderr).strip()
        ok = (r.returncode == 0 and o == want) if rc == 0 else (r.returncode != 0 and want in o)
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
