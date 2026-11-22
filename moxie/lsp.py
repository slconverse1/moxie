"""A small language server for moxie (Language Server Protocol over stdio).  Run: python3 -m moxie lsp [--gc]

It gives an editor three things: diagnostics (the same errors and warnings as `moxie check`, as you type), formatting (the same
layout as `moxie fmt`), and an outline (declarations, for the outline view and "go to symbol").  Documents are synced whole, so
there is no state to get wrong.  Standard library only."""
import json, os, re, sys
from urllib.parse import unquote, urlparse

DECL = re.compile(r"^(?:export\s+)?(?:(?:pure|inline|tailrec|dynamic|unsafe|static|forward)\s+)*"
                  r"(fn|fiber(?:\[\d+\])?\s+fn|tuple|enum|interface|type|impl|unit|test)\s+([A-Za-z_][A-Za-z0-9_]*)?")
KINDS = {"fn": 12, "tuple": 23, "enum": 10, "interface": 11, "type": 5, "impl": 5, "unit": 14, "test": 12}


def path_of(uri):
    return unquote(urlparse(uri).path) if uri.startswith("file:") else ""


def diagnostics(src, path):
    """[(line0, col0, endcol0, severity, message)] for one document (severity 1 error, 2 warning)."""
    from .interp import Interp
    from .lexer import MoxieSyntaxError
    import io
    I = Interp(out=io.StringIO(), err=io.StringIO(), search_dir=os.path.dirname(path) if path else ".")
    name = os.path.basename(path) or "<input>"
    try:
        prog = I.load_source(src, name)
    except MoxieSyntaxError as e:
        line = max(e.line - 1, 0)
        col = max(e.col - 1, 0)
        return [(line, col, col + 1, 1, e.msg)]
    except Exception as e:                                     # a checker crash must not kill the editor session
        return [(0, 0, 1, 2, f"internal error while loading: {e}")]
    try:
        found = I.static_check(prog)
    except Exception as e:
        return [(0, 0, 1, 2, f"internal error while checking: {e}")]
    lines = src.split("\n")
    out = []
    for d in found:
        n = max(int(d.line) - 1, 0) if isinstance(d.line, int) else 0
        text = lines[n] if n < len(lines) else ""
        start = len(text) - len(text.lstrip())
        out.append((n, start, max(len(text), start + 1), 2 if d.kind == "warning" else 1, d.msg))
    return out


def symbols(src):
    out = []
    for i, text in enumerate(src.split("\n")):
        m = DECL.match(text)
        if not m:
            continue
        kind = m.group(1).split("[")[0].split()[0]
        name = m.group(2) or ("test " + text.split(None, 1)[1].strip('" ') if kind == "test" and " " in text else kind)
        if kind == "fiber":
            kind = "fn"
        rng = {"start": {"line": i, "character": 0}, "end": {"line": i, "character": len(text)}}
        out.append({"name": name, "kind": KINDS.get(kind, 12), "range": rng, "selectionRange": rng})
    return out


def formatting(src, path):
    from .fmt import format_source
    try:
        new = format_source(src, os.path.basename(path) or "<input>")
    except Exception:
        return []
    if new == src:
        return []
    n = src.count("\n")
    return [{"range": {"start": {"line": 0, "character": 0}, "end": {"line": n + 1, "character": 0}}, "newText": new}]


class Server:
    def __init__(self, inp, out):
        self.inp, self.out = inp, out
        self.docs = {}
        self.down = False

    def read(self):
        length = None
        while True:
            line = self.inp.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                break
            if line.lower().startswith(b"content-length:"):
                length = int(line.split(b":")[1])
        if length is None:
            return None
        return json.loads(self.inp.read(length).decode("utf-8"))

    def send(self, msg):
        data = json.dumps(msg).encode("utf-8")
        self.out.write(b"Content-Length: %d\r\n\r\n" % len(data) + data)
        self.out.flush()

    def publish(self, uri):
        src = self.docs.get(uri, "")
        ds = diagnostics(src, path_of(uri)) if uri in self.docs else []
        self.send({"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics", "params": {"uri": uri, "diagnostics": [
            {"range": {"start": {"line": l, "character": c}, "end": {"line": l, "character": e}}, "severity": sev,
             "source": "moxie", "message": msg} for l, c, e, sev, msg in ds]}})

    def handle(self, m):
        method, p, rid = m.get("method"), m.get("params") or {}, m.get("id")
        reply = lambda r: rid is not None and self.send({"jsonrpc": "2.0", "id": rid, "result": r})
        if method == "initialize":
            reply({"capabilities": {"textDocumentSync": {"openClose": True, "change": 1, "save": {}},
                                    "documentFormattingProvider": True, "documentSymbolProvider": True},
                   "serverInfo": {"name": "moxie-lsp"}})
        elif method == "shutdown":
            self.down = True
            reply(None)
        elif method == "exit":
            return False
        elif method == "textDocument/didOpen":
            d = p["textDocument"]
            self.docs[d["uri"]] = d["text"]
            self.publish(d["uri"])
        elif method == "textDocument/didChange":
            uri = p["textDocument"]["uri"]
            self.docs[uri] = p["contentChanges"][-1]["text"]
            self.publish(uri)
        elif method == "textDocument/didSave":
            uri = p["textDocument"]["uri"]
            if "text" in p:
                self.docs[uri] = p["text"]
            self.publish(uri)
        elif method == "textDocument/didClose":
            uri = p["textDocument"]["uri"]
            self.docs.pop(uri, None)
            self.send({"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics", "params": {"uri": uri, "diagnostics": []}})
        elif method == "textDocument/formatting":
            uri = p["textDocument"]["uri"]
            reply(formatting(self.docs.get(uri, ""), path_of(uri)))
        elif method == "textDocument/documentSymbol":
            reply(symbols(self.docs.get(p["textDocument"]["uri"], "")))
        elif rid is not None:
            self.send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"unsupported: {method}"}})
        return True

    def run(self):
        while True:
            m = self.read()
            if m is None or self.handle(m) is False:
                return 0 if self.down else 1


def main(argv=None, inp=None, out=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--gc" in argv:
        from .values import GC
        GC[0] = True
    return Server(inp or sys.stdin.buffer, out or sys.stdout.buffer).run()
