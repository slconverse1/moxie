"""Directory and path functions (Spec 19c).  Run: python3 tests/run_fs.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []


def run(src, *flags, cmd="run"):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "main.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, p], cwd=d, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT))
    return r.returncode, r.stdout + r.stderr


def chk(name, got, rc, *words):
    code, out = got
    good = code == rc and all(w in out for w in words)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={code} {out.strip()[:300]}"))
    if not good:
        fails.append(name)


chk("make_dir makes parents and list_dir sorts", run('println(make_dir("a/b/c"))\nprintln(make_dir("a/b/c"))\nprintln(write_file("a/z.txt", "1"))\nprintln(list_dir("a"))\n'), 0, 'Ok(())\nOk(())\nOk(())\nOk(Array("b", "z.txt"))')
chk("file_info gives kind and size", run('write_file("f", "hello")\nprintln(file_info("f"))\nmake_dir("d")\nwhen file_info("d")\n  Ok(i) -> println("${i.kind} ${i.is_dir()} ${i.is_file()}")\n  Err(e) -> println(e)\n'), 0, 'FileInfo(kind: "file", size: 5)', "dir true false")
chk("path_exists", run('println(path_exists("nope"))\nwrite_file("x", "")\nprintln(path_exists("x"))\n'), 0, "Ok(false)\nOk(true)")
chk("rename_path moves a file", run('write_file("x", "hi")\nprintln(rename_path("x", "y"))\nprintln(read_file("y"))\nprintln(path_exists("x"))\n'), 0, 'Ok(())\nOk("hi")\nOk(false)')
chk("remove_file and remove_dir", run('make_dir("d")\nwrite_file("d/f", "")\nprintln(remove_dir("d"))\nprintln(remove_file("d/f"))\nprintln(remove_dir("d"))\nprintln(path_exists("d"))\n'), 0, "code: 11", "Ok(())\nOk(false)")
chk("remove_file refuses a directory", run('make_dir("d")\nprintln(remove_file("d"))\n'), 0, "is a directory")
chk("a missing path is NOT_FOUND", run('println(list_dir("nope"))\nprintln(file_info("nope"))\nprintln(remove_file("nope"))\n'), 0, "code: 9")
chk("path_join", run('println(path_join("a", "b"))\nprintln(path_join("a/", "b"))\nprintln(path_join("a", "/b"))\nprintln(path_join("", "b"))\nprintln(path_join("/", "b"))\n'), 0, "a/b\na/b\n/b\nb\n/b")
chk("path_parent", run('println(path_parent("a/b/c"))\nprintln(path_parent("a"))\nprintln(path_parent("/a"))\nprintln(path_parent("/"))\nprintln(path_parent("a/b/"))\n'), 0, "a/b\n\n/\n/\na")
chk("path_name, stem, and ext", run('println(path_name("a/b/c.tar.gz"))\nprintln(path_stem("a/b/c.tar.gz"))\nprintln(path_ext("a/b/c.tar.gz"))\nprintln(path_ext(".bashrc"))\nprintln(path_stem(".bashrc"))\nprintln(path_ext("noext"))\n'), 0, "c.tar.gz\nc.tar\ngz\n\n.bashrc\n\n")
chk("a read grant allows list_dir but not make_dir", run('make_dir("d")\nprintln(list_dir("d"))\nprintln(make_dir("e"))\n', "--allow-read=.", "--allow-write=d"), 0, "Ok(Array())", "code: 10", "fs.write is not permitted")
chk("rename needs write on both paths", run('write_file("x", "")\nprintln(rename_path("x", "../y"))\n', "--allow-read", "--allow-write=."), 0, "code: 10")
chk("make_dir without a grant is a compile error", run('println(make_dir("d"))\n', "--deny-all"), 2, "needs fs.read or fs.write")
chk("list_dir without a grant is a compile error", run('println(list_dir("."))\n', "--deny-all"), 2, "needs fs.read or fs.write")
chk("path functions need no grant", run('println(path_join("a", "b"))\n', "--deny-all"), 0, "a/b")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
