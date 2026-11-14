"""json: the closed `Dyn` type (moxie/std/json.mxi), in both dialects.  Run: python3 tests/run_json.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, gc=False):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
DOC = 'import json\nd = json.parse("{\\"name\\": \\"Al\\", \\"age\\": 30, \\"tags\\": [1, 2.5, true, null], \\"n\\": {\\"k\\": 3}}")?\n'
def wrap(body):
    return 'import json\ndynamic fn go() Result[Unit, Error]\n  d = json.parse("{\\"name\\": \\"Al\\", \\"age\\": 30, \\"tags\\": [1, 2.5, true, null], \\"n\\": {\\"k\\": 3}}")?\n' + "".join("  " + l + "\n" for l in body.split("\n")) + "  Ok(())\nprintln(go())\n"
CASES = [
 ("round trip", 'import json\nprintln(json.parse("{\\"a\\": [1, 2.5, true, null, \\"x\\"], \\"b\\": {}}").map((d) -> d.to_json()))\n',
  'Ok("{\\"a\\":[1,2.5,true,null,\\"x\\"],\\"b\\":{}}")'),
 ("field and as_text", wrap('println(d.field("name").flat_map((x) -> x.as_text()))'), 'Ok("Al")\nOk(())'),
 ("nested lookup", wrap('println(d.field("n").flat_map((x) -> x.field("k")).flat_map((x) -> x.as_int()))'), "Ok(3)\nOk(())"),
 ("list element", wrap('println(d.field("tags").flat_map((x) -> x.at(1)).flat_map((x) -> x.as_float()))'), "Ok(2.5)\nOk(())"),
 ("an Int reads as a Float", wrap('println(d.field("age").flat_map((x) -> x.as_float()))'), "Ok(30.0)\nOk(())"),
 ("missing key is an Err", wrap('println(d.field("zzz"))'), 'Err(Error(code: 4, message: "no key \\"zzz\\""))\nOk(())'),
 ("wrong kind is an Err", wrap('println(d.field("name").flat_map((x) -> x.as_int()))'), 'Err(Error(code: 1, message: "not an Int"))\nOk(())'),
 ("index out of range", wrap('println(d.field("tags").flat_map((x) -> x.at(9)))'), 'Err(Error(code: 4, message: "no such element"))\nOk(())'),
 ("is_null", wrap('println(d.field("tags").flat_map((x) -> x.at(3)).map((x) -> x.is_null()))'), "Ok(true)\nOk(())"),
 ("escapes", 'import json\nprintln(json.parse("\\"a\\\\nb\\\\\\"c\\"").map((d) -> d.to_json()))\n', 'Ok("\\"a\\\\nb\\\\\\"c\\"")'),
 ("whitespace around a value", 'import json\nprintln(json.parse("  7 ").map((d) -> d.to_json()))\n', 'Ok("7")'),
 ("truncated list", 'import json\nprintln(json.parse("[1, 2"))\n', "unterminated list"),
 ("missing colon", 'import json\nprintln(json.parse("{\\"a\\" 1}"))\n', "expected `:`"),
 ("extra text", 'import json\nprintln(json.parse("[1] x"))\n', "extra text after the value"),
 ("unterminated string", 'import json\nprintln(json.parse("\\"abc"))\n', "unterminated string"),
 ("empty text", 'import json\nprintln(json.parse(""))\n', "unexpected end of text"),
]
fails = []
for name, src, want in CASES:
    for gc in (False, True):
        rc, out = run(src, gc)
        good = rc == 0 and want in out
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
        if not good:
            fails.append(name)
sys.exit(1 if fails else 0)
