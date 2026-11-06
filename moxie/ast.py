"""AST node definitions for Moxie."""


class N:
    __slots__ = ("line",)
    _fields = ()

    def __repr__(self):
        inner = ", ".join(f"{f}={getattr(self, f, None)!r}" for f in self._fields)
        return f"{type(self).__name__}({inner})"


def _make(name, fields):
    fields = tuple(fields.split()) if isinstance(fields, str) else tuple(fields)

    def __init__(self, *args, line=0, **kw):
        if len(args) > len(fields):
            raise TypeError(f"{name} takes {len(fields)} fields")
        for f, a in zip(fields, args):
            setattr(self, f, a)
        for f in fields[len(args):]:
            setattr(self, f, kw.pop(f, None))
        if kw:
            raise TypeError(f"{name}: unknown fields {list(kw)}")
        self.line = line
        if name == "Lambda":
            self.partial = False     # made by a call with `_` (takes the callee's effects)
            self.fiber = False       # the body of an inline `run fn (...)`

    extra = ("partial", "fiber") if name == "Lambda" else ()
    cls = type(name, (N,), {"__slots__": fields + extra, "_fields": fields, "__init__": __init__})
    return cls


def _defs():
    g = globals()
    spec = {
        # literals
        "IntLit": "v suffix",
        "FloatLit": "v suffix",
        "DecLit": "text",
        "StrLit": "parts",          # parts: list of str | Interp
        "Interp": "expr spec src",
        "CharLit": "c",
        "BytesLit": "b",
        "ByteChar": "v",
        "KwLit": "name",
        "DurLit": "v unit",
        "BoolLit": "b",
        "UnitLit": "",
        # names
        "Name": "name",
        "PH": "idx",               # _ or _1 _2 ... placeholder
        "Slot": "",                # & in a pipe call
        "Gimme": "n name",
        "Dollar": "expr",          # $name : variable used as a Dict key
        # compound
        "TupleE": "items",         # items: list of (label, expr, spread)
        "MArr": "rows",
        "Call": "fn args trailing",  # args: list of Arg
        "Arg": "label expr mod",   # mod: None 'ref' 'using' 'spread' 'move'
        "GenApp": "base groups",
        "Field": "obj name",
        "Unary": "op e",
        "Binary": "op l r",
        "AndE": "l r",
        "OrE": "l r",
        "InOp": "l r neg",
        "IsOp": "e pat",
        "RangeE": "lo hi incl",
        "Pipe": "l stage",
        "Tick": "l fname r",
        "Q": "e",
        "IfE": "branches else_",       # branches: [(cond, body)]
        "WhenE": "scrut arms",         # arms: [Arm]
        "Arm": "pats guard body",
        "SeqE": "arms",                # [(pred, stage)]
        "SelectE": "arms",             # [SelArm]
        "SelArm": "kind bind expr body",   # kind: read closed cancelled default expr
        "ForE": "pat iter body else_ label",
        "WhileE": "cond body else_ label",
        "ForAll": "binds body",          # binds: list of (name, type)
        "DaemonE": "body",
        "ScopeE": "name body",         # scope NAME: ... (NAME is the scope's Cancel token, or None)
        "DoE": "body label",
        "DoRecv": "recv kind body",    # kind: do | update
        "UpdLine": "name expr nested",
        "ForM": "lines yield_",        # lines: [(kind, pat, expr, else_)]
        "CompE": "kind elem key pat iter cond",
        "Block": "stmts",
        "Lambda": "params body recv locals ret",
        "Param": "pat name type default mod variadic",
        "RunE": "target limit",
        "TodoE": "msg",
        "PathE": "segs",
        "SqlE": "conn parts",
        "Ref": "e",                    # prefix ref
        "Move": "e",
        "Deref": "e",                  # @atom
        # statements
        "Assign": "targets value ann op vis",
        "ElseLet": "pat value else_",
        "Incr": "target delta",
        "Return": "e",
        "Break": "label e daemon",
        "Continue": "label",
        "TrailIf": "stmt cond",
        "ExprStmt": "e",
        # declarations
        "FnDecl": "name tparams params ret locals body flags clauses alias guard contracts",
        "FnGroup": "name clauses",
        "TupleDecl": "name tparams fields derivs positional vis invariants",
        "FieldDecl": "name type default delegate",
        "EnumDecl": "name tparams header cases derivs vis",
        "CaseDecl": "name fields",
        "IfaceDecl": "name tparams members embeds vis",
        "ImplDecl": "iface target tparams members bodyless",
        "AliasDecl": "kind name tparams type vis",
        "ImportDecl": "pkg alias names",
        "UsingDecl": "name expr",
        "InitDecl": "body",
        "TestDecl": "name body",
        "ForwardDecl": "fn",
        "ForeignDecl": "lib fns handles",
        "TParam": "name holes bounds where",
        # patterns
        "PWild": "",
        "PBind": "name",
        "PLit": "expr",
        "PRange": "lo hi incl",
        "PTuple": "items",             # items: list of (label, pat)
        "PCon": "path args",           # args: list of (label, pat)
        "PAs": "name pat",
        "PPin": "expr",
        "PRel": "op operand",
        "PRest": "name",
        "PPlace": "expr",
        "PTyped": "pat type",
        "PBin": "elems",               # binary pattern: [("lit", [byte, ...]) | ("field", name|None, kind, arg)]
        # types
        "TName": "path groups",
        "TTuple": "items",
        "TFn": "params ret recv",
        "TUnion": "members",
        "TAny": "iface",
        "TStatic": "inner",
        "TBound": "name iface",          # X: Show  in a type-function pattern: any type that implements Show, bound to X
        "TMatch": "scrut arms",          # when T: pattern -> type ...  (a type function; arms are (pattern, result) pairs)
        "TLambda": "params body",        # [A, M[_]] -> T: a type-level function (params are TParam)
        "TApp": "fn groups",             # ([A] -> T)[Int]: a lambda applied where it is written
        "THole": "",
        "TUnit": "",
        "TExpr": "expr",
    }
    for k, v in spec.items():
        g[k] = _make(k, v)


_defs()
