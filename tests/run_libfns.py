"""ok_or, ok, drop_last, find_map, position.  Run: python3 tests/run_libfns.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=(), cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    return r.returncode, (r.stdout + r.stderr).decode()

fails = []
def chk(name, src, rc_want, *wants, cmd="run"):
    for flags in ((), ("--gc",)):
        rc, out = run(src, flags, cmd)
        ok = rc == rc_want and all(w in out for w in wants)
        label = name + (" (gc)" if flags else "")
        print(("ok    " if ok else "FAIL  ") + label + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
        if not ok: fails.append(label)

H = 'o Option[Int] = Some(1)\nn Option[Int] = None\nr Result[Int, Error] = Ok(4)\ne Result[Int, Error] = Err(Error(1, "x"))\nxs = List(1, 2, 3, 4)\n'
chk("ok_or", H + 'println(o |> ok_or(Error(7, "none")))\nprintln(n |> ok_or(Error(7, "none")))\n', 0, 'Ok(1)', 'Err(Error(code: 7, message: "none"))')
chk("ok", H + 'println(r |> ok())\nprintln(e |> ok())\n', 0, "Some(4)\nNone")
chk("drop_last", H + 'println(xs |> drop_last(1) |> collect())\nprintln(xs |> drop_last(0) |> collect())\nprintln(xs |> drop_last(9) |> collect())\n', 0, "List(1, 2, 3)\nList(1, 2, 3, 4)\nList()")
chk("find_map", H + 'println(xs |> find_map((x) -> if x > 2 then Some(x * 10) else None))\nprintln(xs |> find_map((x) -> if x > 9 then Some(x) else None))\n', 0, "Ok(30)", "Err(")
chk("position", H + 'println(xs |> position(_ > 2))\nprintln(xs |> position(_ > 9))\n', 0, "Ok(2)", "Err(")
chk("ok_or has a Result type", H + 'x Int = o |> ok_or(Error(1, "a"))\n', 1, "mismatched types", cmd="check")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
