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


EFFECT_VALUES = ("pure", "prints", "parks", "impure", "prints parks", "parks prints")
FUNCTION_KEYS = {"effects": "one of " + ", ".join(f'"{e}"' for e in EFFECT_VALUES),
                 "skip": "true or false", "pair": 'a list of two names, ["buf", "len"]',
                 "returns": '"status" or "value"', "outs": "a list of parameter names", "rename": "a name",
                 "keeps": "a list of callback parameter names that the library keeps"}
HANDLE_KEYS = {"closes": "the name of a C function"}
TOP_KEYS = {"lib": "the library name", "functions": "tables, one per C function",
            "handles": "tables, one per handle type"}


class SidecarError(Exception):
    pass


def _suggest(word, choices):
    import difflib
    m = difflib.get_close_matches(word, list(choices), n=1)
    return f" (did you mean '{m[0]}'?)" if m else ""


def validate_sidecar(side):
    """Check the shape of bindgen.toml; returns a list of problems (empty when it is fine)."""
    errs = []
    for k in side:
        if k not in TOP_KEYS:
            errs.append(f"unknown key '{k}'{_suggest(k, TOP_KEYS)}; the keys are lib, [functions.NAME], and [handles.TYPE]")
    if "lib" in side and not isinstance(side["lib"], str):
        errs.append("lib must be a string")
    for tbl, keys in (("functions", FUNCTION_KEYS), ("handles", HANDLE_KEYS)):
        t = side.get(tbl, {})
        if not isinstance(t, dict):
            errs.append(f"[{tbl}] must be a table of tables, such as [{tbl}.NAME]")
            continue
        for name, spec in t.items():
            if not isinstance(spec, dict):
                errs.append(f"[{tbl}.{name}] must be a table")
                continue
            for k, v in spec.items():
                if k not in keys:
                    errs.append(f"[{tbl}.{name}]: unknown key '{k}'{_suggest(k, keys)}; the keys are {', '.join(keys)}")
                    continue
                ok = True
                if k == "effects":
                    ok = v in EFFECT_VALUES
                elif k == "skip":
                    ok = isinstance(v, bool)
                elif k == "pair":
                    ok = isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v)
                elif k == "returns":
                    ok = v in ("status", "value")
                elif k in ("outs", "keeps"):
                    ok = isinstance(v, list) and all(isinstance(x, str) for x in v)
                elif k in ("rename", "closes"):
                    ok = isinstance(v, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", v) is not None
                if not ok:
                    errs.append(f"[{tbl}.{name}]: {k} must be {keys[k]}")
    return errs


def load_sidecar(path):
    if path and os.path.exists(path):
        import tomllib
        try:
            with open(path, "rb") as f:
                side = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise SidecarError(f"{path}: {e}")
        errs = validate_sidecar(side)
        if errs:
            raise SidecarError("\n".join(f"{path}: {e}" for e in errs))
        return side
    return {}


def unused_sidecar(side, decls, handles_used, all_c_functions):
    """Entries that match nothing: usually a typo, or a function the library dropped."""
    out = []
    for name in side.get("functions", {}):
        if name not in all_c_functions:
            out.append(f"[functions.{name}] matches no function in the header{_suggest(name, all_c_functions)}")
    for name in side.get("handles", {}):
        if name not in handles_used:
            out.append(f"[handles.{name}] matches no handle type in the generated bindings{_suggest(name, handles_used)}")
    return out


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
        self.fn_info = {}       # function -> facts for --wrap
        self.c_functions = set()  # every function the header declares
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
                return self.callback(t)
            else:
                break
        if isinstance(t, c.IdentifierType):
            mt, nm = self.base_name(t)
            if mt is None and nm in self.typedefs:           # typedef: resolve once
                d = self.desc(self.typedefs[nm], is_param)
                if ptr == 0:
                    return d
                if ptr == 2 and d[0] == "opaque":
                    return ("out_handle", d[1], d[2], const)
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
                if ptr == 2:
                    return ("out_handle", hn, name, const)
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

    def callback(self, ft):
        """A function-pointer parameter becomes a function type. A `void *` is the user-data pointer
        (UserData: the closure carries its own context), and a byte pointer followed by an integer
        length is one Array[Byte]."""
        c = self.c
        raw = []
        if ft.args:
            for p in ft.args.params:
                if isinstance(p, c_ellipsis(c)):
                    raise Todo("a callback with a variadic signature cannot be declared")
                if isinstance(p, c.Typename) and isinstance(p.type, c.TypeDecl) \
                        and isinstance(p.type.type, c.IdentifierType) and p.type.type.names == ["void"] \
                        and len(ft.args.params) == 1:
                    break
                raw.append((self.pname(getattr(p, "name", None), len(raw)), self.desc(p.type)))
        ps, i = [], 0
        while i < len(raw):
            pn, d = raw[i]
            if d[0] in ("scalar", "struct"):
                ps.append(d[1])
            elif d[0] == "bytes" and d[2] == "void":
                ps.append("UserData")
            elif d[0] == "bytes" and i + 1 < len(raw) and raw[i + 1][1][0] == "scalar" \
                    and raw[i + 1][1][1] not in ("Float", "Double", "Bool"):
                ps += ["Array[Byte]", raw[i + 1][1][1]]
                i += 1
            else:
                raise Todo("a callback takes a pointer that is neither user data nor a buffer with a length, which is not supported")
            i += 1
        r = self.desc(ft.type, False)
        if r[0] == "void":
            rt = "Unit"
        elif r[0] in ("scalar", "struct"):
            rt = r[1]
        else:
            raise Todo("a callback returns a pointer, which is not supported")
        return ("callback", f"({', '.join(ps)}) -> {rt}", "callback", False, ps, rt)

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
        outh = None
        hs = set()
        info = {"ps": [], "outh": None}          # for --wrap: the visible parameters, in order
        self.fn_handles[name] = hs
        while i < len(params):
            pn, d = params[i]
            k = d[0]
            if k == "bytes" and d[2] == "void" and any(q[1][0] == "callback" for q in params) \
                    and not (i + 1 < len(params) and params[i + 1][1][0] == "scalar" and LEN_NAMES.search(params[i + 1][0])):
                out.append(f"{pn}: UserData")          # the user-data pointer that goes with a callback
                i += 1
                continue
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
                info["ps"].append((pn, "bytes_ro" if d[3] else "bytes_rw", "Array[Byte]"))
                i += 2
                continue
            if k == "scalar":
                out.append(f"{pn}: {d[1]}")
                info["ps"].append((pn, "val", d[1]))
            elif k == "cstring":
                out.append(f"{pn}: CString")
                info["ps"].append((pn, "cstring", "CString"))
            elif k == "struct":
                out.append(f"{pn}: {d[1]}")
                info["ps"].append((pn, "val", d[1]))
            elif k in ("scalar_ptr", "struct_ptr"):
                if d[3]:
                    # const pointer to a scalar: an array of them, which is not supported yet
                    raise Todo(f"parameter '{pn}' is a const pointer to {d[2]} (an array input), which is not supported yet")
                out.append(f"ref {pn}: {d[1]}")
                info["ps"].append((pn, "ref_" + ("scalar" if k == "scalar_ptr" else "struct"), d[1]))
            elif k == "out_handle":
                if outh is not None:
                    raise Todo("more than one out-handle parameter is not supported")
                outh = d[1]
                out.append(f"ref {pn}: {d[1]}")
                hs.add(d[1])
                info["outh"] = d[1]
            elif k == "callback" and pn in (sc.get("keeps") or []):
                if d[5] != "Unit":
                    raise Todo(f"callback '{pn}' is kept by the library but returns a value, so it cannot be delivered as events")
                vals = [x for x in clean_cb(d[1]).split(") -> ")[0][1:].split(", ") if x]
                if not vals:
                    raise Todo(f"callback '{pn}' is kept by the library but carries no values to deliver")
                payload = d[4][0] if len(d[4]) == 1 else "(" + ", ".join(d[4]) + ")"
                wpayload = vals[0] if len(vals) == 1 else "(" + ", ".join(vals) + ")"
                out.append(f"{pn}: Events[{payload}]")
                info["ps"].append((pn, "events", wpayload))
            elif k == "callback":
                out.append(f"{pn}: {d[1]}")
                info["ps"].append((pn, "val", d[1]))
            elif k == "opaque_ptr":
                out.append(f"{pn}: {d[1]}")
                hs.add(d[1])
                info["ps"].append((pn, "val", d[1]))
            else:
                raise Todo(f"parameter '{pn}' has an unsupported type")
            i += 1
        rk = ret[0]
        if outh is not None:
            if rk == "void":
                rtxt = f" {outh}"
            elif rk == "scalar" and ret[1] in ("Int32", "Int", "Int64", "UInt32"):
                rtxt = f" Result[{outh}, Error]"
            else:
                raise Todo("a function with an out-handle must return void or an int status")
        elif rk == "void":
            rtxt = ""
        elif rk in ("scalar", "struct"):
            rtxt = " " + ret[1]
        elif rk == "opaque_ptr":
            rtxt = f" Result[{ret[1]}, Error]"
            hs.add(ret[1])
        else:
            raise Todo("the result is a pointer, which is not supported yet")
        eff = sc.get("effects", "impure")
        info.update(eff=eff, rtxt=rtxt.strip(), rk=rk, rt=ret[1] if len(ret) > 1 else None, sc=sc)
        self.fn_info[name] = info
        return f"internal {eff} fn {name}({', '.join(out)}){rtxt}"


ZERO = {"Int8": "0i8", "Int16": "0i16", "Int32": "0i32", "Int64": "0i64", "UInt8": "0u8", "UInt16": "0u16",
        "UInt32": "0u32", "UInt64": "0u64", "Int": "0", "UInt": "cast[UInt](0)", "Float": "0.0f", "Double": "0.0",
        "Bool": "false", "Byte": "0u8"}
OUT_NAMES = re.compile(r"^(out|result|res|ret)$|(^|_)(out|result|res|ret)$|^p?out(put)?", re.I)
STATUS_TYPES = ("Int32", "Int", "Int64", "UInt32")


def wrapper_names(decls, lib, taken, side=None):
    """The exported name for each raw function: the library prefix removed, or `lib_name` when that would clash."""
    from .prelude import REG
    pre = re.sub(r"[^a-z0-9]", "", lib.lower())
    names, used = {}, set(decls) | set(taken)
    side = side or {}
    for n in decls:
        cand = n
        if pre and n.startswith(pre + "_") and len(n) > len(pre) + 1:
            cand = n[len(pre) + 1:]
        elif pre and n.startswith(pre) and len(n) > len(pre) and n[len(pre)].isupper():
            cand = n[len(pre)].lower() + n[len(pre) + 1:]
        clash = (not cand or not cand[0].islower() or cand in HARD or cand in REG or cand in ("open", "main")
                 or cand in used or cand in names.values())
        if cand == n:                       # no prefix to remove: the raw name is taken by the declaration
            cand = f"{pre}_{n}"
        elif clash:                         # would hide a prelude function or repeat a name
            cand = cand + "_" if cand and cand[0].islower() else f"{pre}_{n}"
        while cand in used or cand in names.values():
            cand += "_"
        names[n] = cand
        if side.get("functions", {}).get(n, {}).get("rename"):
            names[n] = side["functions"][n]["rename"]
    return names


def clean_cb(ty):
    """A callback's type as the moxie function sees it: no UserData, and no length after an Array[Byte]."""
    if not ty.startswith("(") or " -> " not in ty:
        return ty
    inner, ret = ty[1:].split(") -> ", 1)
    ps = [x.strip() for x in inner.split(",")] if inner.strip() else []
    out, i = [], 0
    while i < len(ps):
        if ps[i] == "UserData":
            i += 1
        elif ps[i] == "Array[Byte]":
            out.append(ps[i])
            i += 2
        else:
            out.append(ps[i])
            i += 1
    return "(" + ", ".join(out) + ") -> " + ret


def make_wrappers(g, decls, lib, side, comments):
    """Default wrappers (Spec 19a): text conversion, and a Result for the usual C conventions.
    Returns (text, report lines)."""
    taken = set(g.tuples) | set(n for n, _ in g.enums)
    names = wrapper_names(decls, lib, taken, side)
    lines = [f"// Generated by moxie bindgen --wrap for the {lib} bindings.",
             "// Wrappers follow common C habits: a CString parameter is a String; an int status where 0 is success,",
             "// with out-parameters, becomes a Result; everything else is passed through.  Correct a guess with",
             "// returns = \"status\" | \"value\" or outs = [\"name\"] under [functions.NAME] in bindgen.toml, then run again.",
             ""]
    report = []
    for name in decls:
        info = g.fn_info.get(name)
        if info is None:
            continue
        sc = info["sc"]
        w = names[name]
        ps = info["ps"]
        forced_outs = sc.get("outs")
        def is_out(p):
            if not p[1].startswith("ref_") or p[1] != "ref_scalar":
                return False
            return (p[0] in forced_outs) if forced_outs is not None else bool(OUT_NAMES.search(p[0]))
        outs = [p for p in ps if is_out(p)]
        mode = sc.get("returns")
        if mode is None:
            mode = "status" if (outs and info["rk"] == "scalar" and info["rt"] in STATUS_TYPES) else "value"
        if mode == "status" and not (info["rk"] == "scalar" and info["rt"] in STATUS_TYPES):
            mode = "value"
        if info["outh"] is not None:
            mode = "value"                      # an out-handle is already a Result from the raw declaration
        if mode == "value":
            outs = []
        sig, call = [], []
        for p in ps:
            pn, kind, ty = p
            if p in outs:
                call.append(f"ref {pn}")
                continue
            if kind == "cstring":
                sig.append(f"{pn}: String")
                call.append(f"cstr({pn})")
            elif kind in ("bytes_rw", "ref_scalar", "ref_struct"):
                sig.append(f"ref {pn}: {ty}")
                call.append(f"ref {pn}")
            elif kind == "events":
                sig.append(f"{pn}: ChanW[{ty}]")
                call.append(f"move {pn}")
            else:
                sig.append(f"{pn}: {clean_cb(ty)}")
                call.append(pn)
        for cl in comments.get(name, "").split("\n"):
            if cl.strip():
                lines.append(f"/// {cl.strip()}")
        head = f"export {info['eff']} fn {w}({', '.join(sig)})"
        callx = f"{name}({', '.join(call)})"
        zero_ok = all(ZERO.get(p[2]) for p in outs)
        if mode == "status" and zero_ok:
            tys = [p[2] for p in outs]
            rt = tys[0] if len(tys) == 1 else "(" + ", ".join(tys) + ")" if tys else "Unit"
            lines.append(f"{head} Result[{rt}, Error]:")
            for p in outs:
                lines.append(f"  {p[0]} = {ZERO[p[2]]}")
            lines.append(f"  status = {callx}")
            lines.append(f"  if status ~= {ZERO.get(info['rt'], '0')}:")
            lines.append(f"    return fail(status, \"{name} failed\")")
            val = outs[0][0] if len(outs) == 1 else "(" + ", ".join(p[0] for p in outs) + ")" if outs else "()"
            lines.append(f"  Ok({val})")
            report.append(f"  status:  {name} -> {w} (0 is success; result is {rt})")
        else:
            if mode == "status":
                report.append(f"  skipped status for {name}: an out-parameter has no starting value known to bindgen")
            if outs:
                sig2, call2 = [], []
                for p in ps:
                    if p in outs:
                        sig2.append(f"ref {p[0]}: {p[2]}")
                        call2.append(f"ref {p[0]}")
                    elif p[1] == "cstring":
                        sig2.append(f"{p[0]}: String")
                        call2.append(f"cstr({p[0]})")
                    elif p[1] in ("bytes_rw", "ref_scalar", "ref_struct"):
                        sig2.append(f"ref {p[0]}: {p[2]}")
                        call2.append(f"ref {p[0]}")
                    elif p[1] == "events":
                        sig2.append(f"{p[0]}: ChanW[{p[2]}]")
                        call2.append(f"move {p[0]}")
                    else:
                        sig2.append(f"{p[0]}: {clean_cb(p[2])}")
                        call2.append(p[0])
                head = f"export {info['eff']} fn {w}({', '.join(sig2)})"
                callx = f"{name}({', '.join(call2)})"
            r = (" " + info["rtxt"]) if info["rtxt"] else ""
            lines.append(f"{head}{r}: {callx}")
        lines.append("")
    return "\n".join(lines), report


def c_ellipsis(c):
    return c.EllipsisParam


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
            g.c_functions.add(n.name)
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
    generate.last = (g, comments)
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
    wrap = False
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
        elif a == "--wrap":
            wrap = True
        elif a == "-D":
            defines.append(argv[i + 1]); i += 1
        elif a == "-I":
            includes.append(argv[i + 1]); i += 1
        else:
            header = a
        i += 1
    if not header or not (target or pkg):
        err.write("usage: moxie bindgen HEADER (-o FILE | --package NAME) [--lib LIB] [--check] [--wrap] [-D NAME] [-I DIR]\n")
        return 2
    outdir = pkg if pkg else os.path.dirname(os.path.abspath(target))
    bind_path = os.path.join(pkg, "bindings.mxi") if pkg else target
    try:
        side = load_sidecar(os.path.join(outdir, "bindgen.toml"))
    except SidecarError as e:
        err.write(f"moxie bindgen: {e}\n")
        return 2
    lib = lib or side.get("lib") or re.sub(r"\.h$", "", os.path.basename(header))
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
            fl = '"bindings.mxi", "wrappers.mxi", "api.mxi"' if wrap else '"bindings.mxi", "api.mxi"'
            open(mf, "w").write(f'name = "{name}"\nfiles = [{fl}]\n\n[native]\nlibs = ["{lib}"]\n')
        api = os.path.join(pkg, "api.mxi")
        if not os.path.exists(api):
            open(api, "w").write("// Write your wrappers here: exported moxie functions over the internal declarations in bindings.mxi.\n")
    open(bind_path, "w", encoding="utf-8").write(text)
    out.write(f"wrote {bind_path}: {len(decls)} functions declared, {len(todos)} left as todo\n")
    for n, why in todos:
        out.write(f"  todo: {n}: {why}\n")
    g0, _c0 = generate.last
    used_handles = {h for n in decls for h in g0.fn_handles.get(n, ())}
    for msg in unused_sidecar(side, decls, used_handles, g0.c_functions):
        out.write(f"  warning: bindgen.toml: {msg}\n")
    if wrap:
        g, comments = generate.last
        wtext, report = make_wrappers(g, decls, lib, side, comments)
        wpath = os.path.join(os.path.dirname(os.path.abspath(bind_path)), "wrappers.mxi")
        open(wpath, "w", encoding="utf-8").write(wtext)
        out.write(f"wrote {wpath}: {len(decls)} wrappers\n")
        for line in report:
            out.write(line + "\n")
    return 0
