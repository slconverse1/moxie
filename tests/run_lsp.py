"""Language server test: drives `python3 -m moxie lsp` over stdio.  Run: python3 tests/run_lsp.py"""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def frame(m):
    d = json.dumps(m).encode()
    return b"Content-Length: %d\r\n\r\n" % len(d) + d

def session(msgs, *flags):
    p = subprocess.run([sys.executable, "-m", "moxie", *flags, "lsp"], cwd=ROOT, input=b"".join(frame(m) for m in msgs), capture_output=True, timeout=60)
    out, i, res = p.stdout, 0, []
    while i < len(out):
        j = out.index(b"\r\n\r\n", i)
        n = int(out[i:j].split(b":")[1])
        res.append(json.loads(out[j + 4:j + 4 + n]))
        i = j + 4 + n
    return p.returncode, res

fails = []
def chk(name, cond):
    print(("ok    " if cond else "FAIL  ") + name)
    if not cond: fails.append(name)

U = "file:///tmp/x.mxi"
def opened(text):
    return [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "textDocument/didOpen", "params": {"textDocument": {"uri": U, "text": text}}}]
def diags(res): return [m for m in res if m.get("method") == "textDocument/publishDiagnostics"][-1]["params"]["diagnostics"]
END = [{"jsonrpc": "2.0", "id": 99, "method": "shutdown"}, {"jsonrpc": "2.0", "method": "exit"}]

rc, res = session(opened('println("hi")\n') + END)
chk("initialize advertises formatting and symbols", res[0]["result"]["capabilities"]["documentFormattingProvider"] and res[0]["result"]["capabilities"]["documentSymbolProvider"])
chk("a clean file has no diagnostics", diags(res) == [])
chk("clean shutdown exits 0", rc == 0)

rc, res = session(opened('println(1 +\n') + END)
d = diags(res)
chk("a syntax error is reported", len(d) == 1 and d[0]["severity"] == 1 and d[0]["source"] == "moxie")

rc, res = session(opened('x Int = "a"\nprintln(x)\n') + END)
d = diags(res)
chk("a type error is reported on its line", any(e["range"]["start"]["line"] == 0 and e["severity"] == 1 for e in d))

rc, res = session(opened('tuple P\n  a Int\nprintln(P(a: 1))\n') + END)
chk("a missing deriving show is reported", any("no text form" in e["message"] for e in diags(res)))

rc, res = session(opened('println(1 +\n') + [{"jsonrpc": "2.0", "method": "textDocument/didChange", "params": {"textDocument": {"uri": U}, "contentChanges": [{"text": 'println(1)\n'}]}}] + END)
chk("an edit clears the diagnostics", diags(res) == [])

src = 'fn add(a Int,b Int) Int\n  a+b\ntuple P deriving show\n  a Int\nenum E\n  X\n  Y\n'
rc, res = session(opened(src) + [{"jsonrpc": "2.0", "id": 5, "method": "textDocument/documentSymbol", "params": {"textDocument": {"uri": U}}}] + END)
syms = [m for m in res if m.get("id") == 5][0]["result"]
chk("outline lists fn, tuple, enum", [s["name"] for s in syms] == ["add", "P", "E"])

rc, res = session(opened(src) + [{"jsonrpc": "2.0", "id": 6, "method": "textDocument/formatting", "params": {"textDocument": {"uri": U}}}] + END)
edits = [m for m in res if m.get("id") == 6][0]["result"]
chk("formatting returns the moxie fmt layout", len(edits) == 1 and "fn add(a Int, b Int) Int" in edits[0]["newText"])

rc, res = session(opened('println(1)\n') + [{"jsonrpc": "2.0", "id": 7, "method": "nonsense"}] + END)
chk("an unknown request gets an error reply", [m for m in res if m.get("id") == 7][0]["error"]["code"] == -32601)

rc, res = session(opened('xs = List[Int][2](1, 2)\nprintln(xs)\n') + END, "--gc")
chk("--gc changes the rules (no error for a sized list)", isinstance(diags(res), list))
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
