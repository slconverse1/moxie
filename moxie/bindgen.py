"""moxie bindgen: write `foreign` declarations from a C header (Spec section 19a).

  moxie bindgen HEADER [-o FILE | --package NAME] [--lib LIB] [--check] [-D NAME[=VALUE]] [-I DIR]

Uses pycparser (pip install pycparser) after running the C preprocessor.  It handles typical
clean library headers.  Corrections go in `bindgen.toml` next to the output (see below).
"""
import os
import re
import subprocess
import sys

HARD = {"fn", "tuple", "enum", "interface", "impl", "forward", "inline", "fiber", "import", "export",
        "internal", "using", "if", "elif", "else", "when", "select", "for", "while", "in", "is", "break",
        "continue", "return", "daemon", "do", "run", "ref", "move", "static", "and", "or", "not", "true",
        "false", "Self", "self", "todo"}

SCALAR = {
    "char": "Int8", "signed char": "Int8", "unsigned char": "UInt8",
    "short": "Int16", "unsigned short": "UInt16", "int": "Int32", "unsigned int": "UInt32", "unsigned": "UInt32",
    "long": "Int", "unsigned long": "UInt", "long long": "Int64", "unsigned long long": "UInt64",
    "float": "Float", "double": "Double", "_Bool": "Bool",
    "size_t": "UInt", "ssize_t": "Int", "int8_t": "Int8", "uint8_t": "UInt8", "int16_t": "Int16",
    "uint16_t": "UInt16", "int32_t": "Int32", "uint32_t": "UInt32", "int64_t": "Int64", "uint64_t": "UInt64",
    "intptr_t": "Int", "uintptr_t": "UInt", "ptrdiff_t": "Int",
}
BYTE_BASES = {"unsigned char", "uint8_t", "void", "char", "signed char", "int8_t"}
LEN_NAMES = re.compile(r"^(len|length|size|n|count|nbytes|num|sz|buflen|bufsize|nbyte)$|(_len|_size|_length|_count|len|size)$", re.I)


class Todo(Exception):
    pass


def pascal(name):
    parts = [p for p in re.split(r"_+", name) if p]
    return "".join(p[0].upper() + p[1:] for p in parts) or "T"


def load_sidecar(path):
    if path and os.path.exists(path):
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    return {}


def preprocess(header, defines, includes):
    cmd = ["gcc", "-E", "-D__attribute__(x)=", "-D__extension__=", "-D__restrict=", "-D__inline=inline",
           "-D__asm__(x)="]
    for d in defines:
        cmd.append("-D" + d)
    for i in includes:
        cmd.append("-I" + i)
    cmd.append(header)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("moxie bindgen: the C preprocessor failed:\n" + r.stderr[:600])
    return "typedef char *__builtin_va_list;\n" + r.stdout


def header_comments(path):
    """Map function name -> the comment text directly above its declaration."""
    out = {}
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
    except OSError:
        return out
    for i, ln in enumerate(lines):
        st = ln.strip()
        m = re.search(r"\b([A-Za-z_]\w*)\s*\(", ln)
        if not m or st.startswith(("/*", "*", "//", "#")):
            continue
        j = i - 1
        block = []
        if j >= 0 and lines[j].strip().endswith("*/"):
            while j >= 0:
                block.append(lines[j])
                if "/*" in lines[j]:
                    break
                j -= 1
            else:
                block = []
        else:
            while j >= 0 and lines[j].strip().startswith("//"):
                block.append(lines[j])
                j -= 1
        if not block:
            continue
        txt = "\n".join(reversed(block))
        body = re.sub(r"^\s*(/\*+|\*+/|\*|//+)\s?", "", txt, flags=re.M)
        body = re.sub(r"\s*\*+/\s*$", "", body, flags=re.M).strip()
        if body:
            out.setdefault(m.group(1), body)
    return out


class Gen:
    def __init__(self, ast, side):
        from pycparser import c_ast
        self.c = c_ast
        self.ast = ast
        self.side = side
        self.typedefs = {}      # name -> node (the TypeDecl inside)
        self.fn_handles = {}    # function -> handle types it mentions
        self.structs = {}       # struct tag -> list of (field, type node) or None (opaque)
        self.enums = []         # (name, value)
        self.tuples = {}        # moxie name -> [(field, moxie type)]
        self.report = []
        self.index()

    # ------------------------------------------------------------ indexing
    def index(self):
        c = self.c
        for n in self.ast.ext:
            if isinstance(n, c.Typedef):
                self.typedefs[n.name] = n.type
                self.note_struct(n.type)
            elif isinstance(n, c.Decl) and n.name is None:
                self.note_struct(n.type)

    def note_struct(self, t):
        c = self.c
        while isinstance(t, (c.TypeDecl,)):
            t = t.type
        if isinstance(t, c.Struct):
            if t.decls is not None:
                self.structs[t.name or id(t)] = t.decls
            else:
                self.structs.setdefault(t.name, None)
        if isinstance(t, c.Enum) and t.values is not None:
            nxt = 0
            for e in t.values.enumerators:
                if e.value is not None:
                    try:
                        nxt = int(e.value.value, 0)
                    except (ValueError, AttributeError):
                        continue
                self.enums.append((e.name, nxt))
                nxt += 1

    # ------------------------------------------------------------ types
    def base_name(self, idt):
        names = [x for x in idt.names if x not in ("const", "volatile")]
        if len(names) == 1 and names[0] in self.typedefs and names[0] not in SCALAR:
            return None, names[0]
        words = list(names)
        if len(words) > 1:
            words = [w for w in words if w != "int" or not ({"short", "long"} & set(words))]
            if "signed" in words and words != ["signed"] and "unsigned" not in words:
                words = [w for w in words if w != "signed"] if len(words) > 1 and words != ["signed", "char"] else words
        key = " ".join(words)
        if key in SCALAR:
            return SCALAR[key], key
        if key == "void":
            return None, "void"
        raise Todo(f"the C type '{' '.join(names)}' has no moxie equivalent")

    def desc(self, t, is_param=True):
        """Describe a C type: (kind, moxie type, extra)."""
        c = self.c
        const = False
        ptr = 0
        while True:
            if isinstance(t, c.PtrDecl):
                ptr += 1
                if t.quals and "const" in t.quals:
                    const = True
                t = t.type
            elif isinstance(t, c.ArrayDecl):
                ptr += 1
                t = t.type
            elif isinstance(t, c.TypeDecl):
                if t.quals and "const" in t.quals:
                    const = True
                t = t.type
            elif isinstance(t, c.FuncDecl):
                raise Todo("a function-pointer parameter is a callback, which is not supported")
            else:
                break
        if isinstance(t, c.IdentifierType):
            mt, nm = self.base_name(t)
            if mt is None and nm in self.typedefs:           # typedef: resolve once
                d = self.desc(self.typedefs[nm], is_param)
                if ptr == 0:
                    return d
                if ptr > 1:
                    raise Todo("pointer to pointer")
                if d[0] == "struct":
                    return ("struct_ptr", d[1], d[2], const)
                if d[0] == "opaque":
                    return ("opaque_ptr", d[1], d[2], const)
                if d[0] == "scalar":
                    under = d[2]
                    if under in ("char", "signed char"):
                        return ("cstring", "CString", under, const) if const else ("bytes", "Array[Byte]", under, const)
                    if under in ("unsigned char", "uint8_t", "int8_t"):
                        return ("bytes", "Array[Byte]", under, const)
                    return ("scalar_ptr", d[1], under, const)
                raise Todo(f"unsupported pointer type '{nm}'")
            if nm == "void":
                if ptr == 0:
                    return ("void", None, "void")
                return ("bytes", "Array[Byte]", "void", const)
            if ptr == 0:
                return ("scalar", mt, nm)
            if ptr == 1:
                if nm == "char" or nm == "signed char":
                    return ("cstring", "CString", nm, const) if const else ("bytes", "Array[Byte]", nm, const)
                if nm in ("unsigned char", "uint8_t", "int8_t"):
                    return ("bytes", "Array[Byte]", nm, const)
                return ("scalar_ptr", mt, nm, const)
            raise Todo("pointer to pointer")
        if isinstance(t, c.Struct):
            name = t.name
            decls = t.decls if t.decls is not None else self.structs.get(name)
            if decls is None:
                hn = pascal(name or "Handle")
                return ("opaque", hn, name) if ptr == 0 else ("opaque_ptr", hn, name, const)
            tn = self.make_tuple(t)
            return ("struct", tn, name or tn) if ptr == 0 else ("struct_ptr", tn, name, const)
        if isinstance(t, c.Enum):
            if ptr == 0:
                return ("scalar", "Int32", "enum")
            return ("scalar_ptr", "Int32", "enum", const)
        if isinstance(t, c.Union):
            raise Todo("a union has no moxie equivalent")
        raise Todo("an unsupported C type")

    def bad(self, why):
        raise Todo(why)

    def make_tuple(self, st):
        c = self.c
        decls = st.decls if st.decls is not None else self.structs.get(st.name)
        if decls is None:
            raise Todo(f"struct {st.name} is opaque")
        tn = pascal(st.name or "Anon")
        if tn in self.tuples:
            return tn
        fields = []
        for d in decls:
            if getattr(d, "bitsize", None) is not None:
                raise Todo(f"struct {st.name} has a bitfield")
            kind = self.desc(d.type, False)
            if kind[0] == "scalar":
                fields.append((d.name, kind[1]))
            elif kind[0] == "struct":
                fields.append((d.name, kind[1]))
            else:
                raise Todo(f"struct {st.name}: field '{d.name}' is not a scalar or a struct of scalars")
        self.tuples[tn] = fields
        return tn

    # ------------------------------------------------------------ functions
    def pname(self, name, i):
        if not name:
            return f"a{i}"
        n = name
        if n[0].isupper():
            n = n[0].lower() + n[1:]
        if n in HARD:
            n += "_"
        return n

    def function(self, decl):
        c = self.c
        name = decl.name
        ft = decl.type
        if not name[0].islower():
            raise Todo(f"the name '{name}' does not start with a lowercase letter, so it is not a moxie function name (renaming is not designed yet)")
        params = []
        if ft.args:
            for i, p in enumerate(ft.args.params):
                if isinstance(p, c.EllipsisParam):
                    raise Todo("a variadic function (printf style) cannot be declared")
                if isinstance(p, c.Typename) and isinstance(p.type, c.TypeDecl) and isinstance(p.type.type, c.IdentifierType) \
                        and p.type.type.names == ["void"] and len(ft.args.params) == 1:
                    break
                params.append((self.pname(getattr(p, "name", None), i), self.desc(p.type)))
        ret = self.desc(ft.type, False)
        sc = self.side.get("functions", {}).get(name, {})
        if sc.get("skip"):
            raise Todo("skipped in bindgen.toml")
        out, i = [], 0
        hs = set()
        self.fn_handles[name] = hs
        while i < len(params):
            pn, d = params[i]
            k = d[0]
            if k == "bytes":
                pair = None
                forced = sc.get("pair")
                if i + 1 < len(params):
                    qn, qd = params[i + 1]
                    if qd[0] == "scalar" and (LEN_NAMES.search(qn) or (forced and forced == [pn, qn])):
                        pair = (qn, qd[1])
                if pair is None:
                    raise Todo(f"parameter '{pn}' is a byte pointer with no length parameter next to it (set pair = [\"{pn}\", \"<length>\"] in bindgen.toml)")
                out.append(f"{'' if d[3] else 'ref '}{pn}: Array[Byte]")
                out.append(f"{pair[0]}: {pair[1]} = len({pn})")
                i += 2
                continue
            if k == "scalar":
                out.append(f"{pn}: {d[1]}")
            elif k == "cstring":
                out.append(f"{pn}: CString")
            elif k == "struct":
                out.append(f"{pn}: {d[1]}")
            elif k in ("scalar_ptr", "struct_ptr"):
                if d[3]:
                    # const pointer to a scalar: an array of them, which is not supported yet
                    raise Todo(f"parameter '{pn}' is a const pointer to {d[2]} (an array input), which is not supported yet")
                out.append(f"ref {pn}: {d[1]}")
            elif k == "opaque_ptr":
                out.append(f"{pn}: {d[1]}")
                hs.add(d[1])
            else:
                raise Todo(f"parameter '{pn}' has an unsupported type")
            i += 1
        rk = ret[0]
        if rk == "void":
            rtxt = ""
        elif rk in ("scalar", "struct"):
            rtxt = " " + ret[1]
        elif rk == "opaque_ptr":
            rtxt = f" Result[{ret[1]}, Error]"
            hs.add(ret[1])
        else:
            raise Todo("the result is a pointer, which is not supported yet")
        eff = sc.get("effects", "impure")
        if eff not in ("pure", "prints", "parks", "impure", "prints parks", "parks prints"):
            eff = "impure"
        return f"internal {eff} fn {name}({', '.join(out)}){rtxt}"


CLOSE_NAMES = re.compile(r"(close|free|destroy|release|finalize|delete|dispose|fini|term)", re.I)


def find_closers(g, decls, side):
    """For each handle type, the function that closes it: from bindgen.toml, else the only
    one-argument function with a closing name that takes the handle and returns nothing or a status."""
    closers = {}
    for h, spec in (side.get("handles") or {}).items():
        if isinstance(spec, dict) and spec.get("closes") in decls:
            closers[h] = spec["closes"]
    for name, hs in g.fn_handles.items():
        if name not in decls or len(hs) != 1:
            continue
        h = next(iter(hs))
        if h in closers or not CLOSE_NAMES.search(name):
            continue
        text = decls[name]
        inner = text[text.index("(") + 1:text.rindex(")")] if ")" in text else ""
        if inner.count(":") == 1 and inner.split(":")[1].strip() == h and "Result[" not in text:
            closers[h] = name
    return closers


def generate(header, lib, side, defines=(), includes=()):
    from pycparser import c_parser
    src = preprocess(header, defines, includes)
    try:
        ast = c_parser.CParser().parse(src)
    except Exception as e:
        raise SystemExit(f"moxie bindgen: cannot parse {header}: {e}")
    g = Gen(ast, side)
    comments = header_comments(header)
    c = g.c
    decls, todos = {}, []
    for n in ast.ext:
        if isinstance(n, c.Decl) and isinstance(n.type, c.FuncDecl) and n.name:
            if "static" in (n.storage or []):
                continue
            cf = getattr(n.coord, "file", None)
            if cf and os.path.basename(cf) != os.path.basename(header):
                continue          # declared in a header that this one includes
            try:
                decls[n.name] = g.function(n)
            except Todo as t:
                todos.append((n.name, str(t)))
    closers = find_closers(g, decls, side)
    for name in list(decls):
        miss = [h for h in g.fn_handles.get(name, ()) if h not in closers]
        if miss:
            del decls[name]
            todos.append((name, f"the handle type {miss[0]} has no closing function (set closes = \"fn\" under [handles.{miss[0]}] in bindgen.toml)"))
    lines = [f"// Generated by moxie bindgen from {os.path.basename(header)}.",
             "// Put corrections in bindgen.toml and run bindgen again; do not edit this file.", ""]
    for tn, fields in g.tuples.items():
        lines.append(f"internal tuple {tn}:")
        for fname, ft in fields:
            lines.append(f"  {fname}: {ft}")
        lines.append("")
    seen = set()
    for en, ev in g.enums:
        if en in seen:
            continue
        seen.add(en)
        lines.append(f"{en} = {ev}")
    if g.enums:
        lines.append("")
    lines.append(f'foreign "{lib}":')
    used = sorted({h for n in decls for h in g.fn_handles.get(n, ())})
    for h in used:
        lines.append(f"  handle {h} closes {closers[h]}")
    for name, text in decls.items():
        for cl in comments.get(name, "").split("\n"):
            if cl.strip():
                lines.append(f"  /// {cl.strip()}")
        lines.append(f"  {text}")
    if not decls:
        lines.append("  // (no functions could be declared)")
    for name, why in todos:
        lines.append(f"  // todo: {name}: {why}")
    lines.append("")
    return "\n".join(lines), decls, todos


def check_drift(new_decls, path):
    """Compare generated declarations with an existing bindings file."""
    old = {}
    if os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            m = re.match(r"\s+(internal .*? fn (\w+)\(.*)$", ln.rstrip())
            if m:
                old[m.group(2)] = m.group(1).strip()
    added = sorted(set(new_decls) - set(old))
    removed = sorted(set(old) - set(new_decls))
    changed = sorted(n for n in set(old) & set(new_decls) if old[n] != new_decls[n].strip())
    return added, removed, changed


def main(argv, out=None, err=None):
    out = out or sys.stdout
    err = err or sys.stderr
    try:
        import pycparser  # noqa
    except ImportError:
        err.write("moxie bindgen needs pycparser: pip install pycparser\n")
        return 2
    header = lib = target = pkg = None
    check = False
    defines, includes = [], []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "-o":
            target = argv[i + 1]; i += 1
        elif a == "--package":
            pkg = argv[i + 1]; i += 1
        elif a == "--lib":
            lib = argv[i + 1]; i += 1
        elif a == "--check":
            check = True
        elif a == "-D":
            defines.append(argv[i + 1]); i += 1
        elif a == "-I":
            includes.append(argv[i + 1]); i += 1
        else:
            header = a
        i += 1
    if not header or not (target or pkg):
        err.write("usage: moxie bindgen HEADER (-o FILE | --package NAME) [--lib LIB] [--check] [-D NAME] [-I DIR]\n")
        return 2
    lib = lib or re.sub(r"\.h$", "", os.path.basename(header))
    outdir = pkg if pkg else os.path.dirname(os.path.abspath(target))
    bind_path = os.path.join(pkg, "bindings.mxi") if pkg else target
    side = load_sidecar(os.path.join(outdir, "bindgen.toml"))
    text, decls, todos = generate(header, lib, side, defines, includes)
    if check:
        added, removed, changed = check_drift(decls, bind_path)
        for lab, items in (("new", added), ("removed", removed), ("changed", changed)):
            for n in items:
                out.write(f"{lab}: {n}\n")
        out.write(f"{len(added)} new, {len(removed)} removed, {len(changed)} changed\n")
        return 1 if (added or removed or changed) else 0
    if pkg:
        os.makedirs(pkg, exist_ok=True)
        name = os.path.basename(os.path.normpath(pkg))
        mf = os.path.join(pkg, "Moxie.toml")
        if not os.path.exists(mf):
            open(mf, "w").write(f'name = "{name}"\nfiles = ["bindings.mxi", "api.mxi"]\n\n[native]\nlibs = ["{lib}"]\n')
        api = os.path.join(pkg, "api.mxi")
        if not os.path.exists(api):
            open(api, "w").write("// Write your wrappers here: exported moxie functions over the internal declarations in bindings.mxi.\n")
    open(bind_path, "w", encoding="utf-8").write(text)
    out.write(f"wrote {bind_path}: {len(decls)} functions declared, {len(todos)} left as todo\n")
    for n, why in todos:
        out.write(f"  todo: {n}: {why}\n")
    return 0
