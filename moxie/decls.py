"""Declarations: functions, tuples, enums, interfaces, impls, imports, tests (mixin)."""
import os
from .ast import *   # noqa
from .values import *   # noqa
from .core import *   # noqa
from .types_ import *   # noqa
from .calls import LazyV, CaseV, RecvCell, USING


PRELUDE_IFACES = {"Functor", "Applicative", "Monad", "Equatable", "Ordered", "FieldHandler", "From", "Show", "Read", "Hashable", "Addable", "Numeric", "Generatable"}


class DeclsMixin:
    # ------------------------------------------------------------ functions
    def note_export(self, env, name, vis):
        if vis in ("export", "internal"):
            self.exports.setdefault(id(env.mod), set()).add(name)

    def ev_FnDecl(self, n, env):
        if n.alias is not None:
            v = yield from self.ev(n.alias, env)
            env.vars[n.name] = v
            return UNIT
        if n.body is None:
            return UNIT      # forward declaration
        env.vars[n.name] = self.make_closure(n, env, n.name)
        for f in n.flags or ():
            if f in ("export", "internal"):
                self.note_export(env, n.name, f)
        return UNIT

    def ev_FnGroup(self, n, env):
        env.vars[n.name] = self.make_closure(n, env, n.name)
        for f in n.clauses[0].flags or ():
            if f in ("export", "internal"):
                self.note_export(env, n.name, f)
        return UNIT
        yield

    def native_rights(self, env):
        """(has_manifest, native table or None, where) for the package whose code is being run."""
        key = self.mod_pkg.get(id(getattr(env, "mod", None) or env))
        if key is None:
            man = self.manifest or {}
            return ("path" in man), man.get("native"), "the entry package"
        return self.pkg_native.get(key, (False, None)) + (f"package '{key}'",)

    def ev_ForeignDecl(self, n, env):
        from .ffi import make_foreign
        has, nat, where = self.native_rights(env)
        if has and nat is None:
            raise Abort(f"{where} declares foreign functions (line {n.line}), but its Moxie.toml has no [native] section; "
                        f"add one with libs = [\"{n.lib}\"]")
        if nat is not None and nat["libs"] is not None and n.lib not in nat["libs"]:
            raise Abort(f"{where} names the native library '{n.lib}' (line {n.line}), which is not in its [native] libs "
                        f"({', '.join(nat['libs']) or 'none'})")
        self.native_dirs = list(nat["paths"]) if nat is not None else []
        ht = self.__dict__.setdefault("handle_types", {})
        hc = self.__dict__.setdefault("handle_closers", {})
        for hname, closer, _ln in n.handles or []:
            ht[hname] = closer
        for d in n.fns:
            env.vars[d.name] = make_foreign(self, n.lib, d)
        for hname, closer, _ln in n.handles or []:
            fobj = env.vars.get(closer)
            if fobj is None:
                raise Abort(f"handle {hname}: the closing function '{closer}' is not declared in this foreign block")
            fobj.closes = hname
            hc[hname] = fobj
            for f in d.flags or ():
                if f in ("export", "internal"):
                    self.note_export(env, d.name, f)
        return Done(UNIT)

    def ev_ForwardDecl(self, n, env):
        return Done(UNIT)

    # ------------------------------------------------------------ tuples
    def ev_TupleDecl(self, n, env):
        fields = n.fields
        if n.positional is not None and not fields:
            fields = [FieldDecl(None, t, None, None) for t in n.positional]
        info = TypeInfo(n.name, n.tparams, fields, n.derivs, n.positional)
        info.env = env
        info.invariants = n.invariants or []
        self.tuples[n.name] = info
        env.vars[n.name] = TypeV(n.name, info)
        self.note_export(env, n.name, n.vis)
        return Done(UNIT)

    def construct(self, t, pos, named, spreads, env, line, hint):
        info = t.info
        if info is None:
            raise Abort(f"cannot construct {t.name}", line)
        if isinstance(info, EnumInfo):
            raise Abort(f"{t.name} is an enum; use one of its cases", line)
        return self.construct_tuple(info, pos, named, spreads, line)

    def construct_tuple(self, info, pos, named, spreads, line):
        fields = info.fields
        nf = len(fields)
        vals = [None] * nf
        have = [False] * nf
        raw = [False] * nf          # True when the value is already a wrapped delegate
        for at, sv in spreads:
            if isinstance(sv, TupleV):
                for i, x in enumerate(sv.vals):
                    nm = sv.names[i] if sv.names else None
                    j = i
                    if nm is not None and info.names and nm in info.names:
                        j = info.names.index(nm)
                    elif nm is not None:
                        raise Abort(f"{info.name} has no field '{nm}'", line)
                    if j < nf:
                        vals[j] = x
                        have[j] = True
                        raw[j] = True
        if len(pos) > nf:
            raise Abort(f"{info.name} takes {nf} fields but {len(pos)} were given", line)
        for i, x in enumerate(pos):
            vals[i] = x
            have[i] = True
            raw[i] = False
        names = info.names
        for k, x in named.items():
            if k not in names:
                raise Abort(f"{info.name} has no field '{k}'", line)
            j = names.index(k)
            vals[j] = x
            have[j] = True
            raw[j] = False
        for j, f in enumerate(fields):
            if not have[j]:
                if f.default is not None:
                    vals[j] = yield from self.evh(f.default, info.env, f.type)
                    have[j] = True
                else:
                    raise Abort(f"missing field '{f.name}' for {info.name}", line)
            if not raw[j]:
                v = vals[j]
                if f.type is not None:
                    v = self.coerce(v, f.type, info.env)
                if f.delegate is not None:
                    dname = self.rtype_name(f.delegate)
                    dinfo = self.tuples.get(dname)
                    dv = TupleV([v], dinfo.names if dinfo else ["value"], dname)
                    ms = self.methods_of(dv, "set_value")
                    if ms:
                        r = yield from self.apply_method(ms[0], dv, [v])
                        nd = self._last_self
                        if isinstance(r, EnumV) and r.et is RESULT_T and r.case == "Err":
                            return r
                        dv = nd
                    v = dv
                vals[j] = v
        tv = TupleV(vals, list(names) if names and names[0] is not None else None, info.name)
        invs = getattr(info, "invariants", None)
        if invs and CONTRACTS[0]:
            ienv = info.env.child()
            for nm, x in zip(names or [], vals):
                if nm is not None:
                    ienv.vars[nm] = x
            for kw, expr, ln, text in invs:
                ok = yield from self.ev(expr, ienv)
                if ok is not True:
                    raise Abort(f"invariant of {info.name} failed: {text} (supplier bug)", line)
        return tv

    # ------------------------------------------------------------ enums
    def ev_EnumDecl(self, n, env):
        et = EnumType(n.name)
        et.consts = {}
        et.header = [p.name for p in n.header] if n.header else None
        et.derivs = n.derivs
        info = EnumInfo(et, n)
        self.enums[n.name] = info
        header_types = [p.type for p in n.header] if n.header else []
        for i, cd in enumerate(n.cases):
            if n.header:
                ci = CaseInfo(cd.name, i, list(et.header), header_types)
            elif cd.fields:
                ci = CaseInfo(cd.name, i, [f.name for f in cd.fields], [f.type for f in cd.fields])
            else:
                ci = CaseInfo(cd.name, i, [])
            et.cases[cd.name] = ci
            et.order.append(cd.name)
            self.cases.setdefault(cd.name, []).append(et)
        env.vars[n.name] = TypeV(n.name, info)
        self.note_export(env, n.name, n.vis)
        if n.header:
            for cd in n.cases:
                ci = et.cases[cd.name]
                pos, named, _, _ = yield from self.eval_case_args(cd.fields or [], env)
                v = self.build_enum(et, ci, pos, named, 0)
                et.consts[cd.name] = v
        return UNIT

    def eval_case_args(self, args, env):
        pos = []
        named = {}
        for a in args:
            v = yield from self.ev(a.expr, env)
            if a.label is None:
                pos.append(v)
            else:
                named[a.label] = v
        return pos, named, {}, []

    def case_value(self, et, ci):
        consts = getattr(et, "consts", None)
        if consts and ci.name in consts:
            return consts[ci.name]
        if ci.fields:
            return CaseV(et, ci)
        return self.enum_instance(et, ci, [])

    def construct_case(self, f, pos, named, spreads, env, line):
        return Done(self.build_enum(f.et, f.ci, pos, named, line))

    def build_enum(self, et, ci, pos, named, line):
        fields = ci.fields
        nf = len(fields)
        if len(pos) > nf:
            raise Abort(f"{et.name}.{ci.name} takes {nf} fields but {len(pos)} were given", line)
        vals = [None] * nf
        for i, x in enumerate(pos):
            vals[i] = x
        for k, x in named.items():
            if k not in fields:
                raise Abort(f"{et.name}.{ci.name} has no field '{k}'", line)
            vals[fields.index(k)] = x
        for j in range(nf):
            if vals[j] is None:
                raise Abort(f"missing field '{fields[j]}' for {et.name}.{ci.name}", line)
            if j < len(ci.ftypes) and ci.ftypes[j] is not None:
                vals[j] = self.coerce(vals[j], ci.ftypes[j], self.module_env)
        return EnumV(et, ci.name, vals, list(fields))

    # ------------------------------------------------------------ aliases
    def ev_AliasDecl(self, n, env):
        kind = n.kind
        self.aliases[n.name] = (kind, n.type, [t.name for t in (n.tparams or [])])
        if kind == "opaque":
            inner = n.type

            def ctor(I, a, kw, ta, inner=inner):
                return I.coerce(a[0], inner, I.module_env)
            env.vars[n.name] = Builtin(ctor, n.name)
        self.note_export(env, n.name, n.vis)
        return Done(UNIT)

    # ------------------------------------------------------------ interfaces and impls
    def ev_IfaceDecl(self, n, env):
        self.ifaces[n.name] = n
        return Done(UNIT)

    def ev_ImplDecl(self, n, env):
        target = n.target
        ifn = n.iface
        if ifn is None and isinstance(target, TName) and (target.path[-1] in self.ifaces or target.path[-1] in PRELUDE_IFACES) and target.groups and target.groups[0]:
            n = ImplDecl(target, target.groups[0][0], n.tparams, n.members, n.bodyless, line=n.line)
            target = n.target
        tname = self.rtype_name(target)
        if tname is None:
            raise Abort("bad impl target", n.line)
        # Self inside the block
        table = self.impls.setdefault(tname, {})
        stat = self.statics.setdefault(tname, {})
        iface_name = None
        if n.iface is not None:
            iface_name = self.rtype_name(n.iface)
            self.iface_impls.setdefault(tname, set()).add(iface_name)
            self._add_embeds(tname, iface_name)
        elif isinstance(target, TName) and target.path[-1] in self.ifaces:
            pass
        members = n.members or []
        for m in members:
            if m.__class__ is AliasDecl:
                continue
            if m.__class__ is FnDecl or m.__class__ is FnGroup:
                node = m
                name = m.name
                flags = m.flags if m.__class__ is FnDecl else m.clauses[0].flags
                if m.__class__ is FnDecl and m.alias is not None:
                    tgt = m.alias
                    if isinstance(tgt, Name) and tgt.name in table:
                        table.setdefault(name, []).extend(table[tgt.name][:1])
                    else:
                        v = yield from self.ev(tgt, env)
                        c = Closure(FnDecl(name, [], [], None, None, None, set(), None, None), env, name)
                        table.setdefault(name, []).append(v if isinstance(v, Closure) else c)
                    continue
                c = Closure(node, env, name)
                c.impl = n
                c.owner = tname
                idecl = self.ifaces.get(iface_name) if iface_name else None
                if idecl is not None:
                    for im in idecl.members or []:
                        if getattr(im, "name", None) == name and getattr(im, "contracts", None):
                            c.iface_contracts = (im.params or [], im.contracts)
                if "static" in (flags or ()):
                    stat.setdefault(name, []).append(c)
                    table.setdefault(name, []).append(c) if False else None
                else:
                    lst = table.setdefault(name, [])
                    lst.append(c)
                if iface_name == "From" and name == "from":
                    st = self.rtype_name(n.iface.groups[0][0]) if n.iface.groups else None
                    self.froms.setdefault(tname, []).append((st, c))
            elif m.__class__ is Assign:
                pass
        # interface defaults
        if iface_name:
            self._install_defaults(tname, iface_name, env)
        return UNIT

    def _add_embeds(self, tname, iface_name):
        d = self.ifaces.get(iface_name)
        if d is None:
            return
        for e in d.embeds or []:
            en = self.rtype_name(e)
            self.iface_impls.setdefault(tname, set()).add(en)
            self._add_embeds(tname, en)

    def _install_defaults(self, tname, iface_name, env):
        d = self.ifaces.get(iface_name)
        if d is None:
            return
        table = self.impls.setdefault(tname, {})
        for m in d.members or []:
            if m.__class__ in (FnDecl, FnGroup):
                node = m
                if m.__class__ is FnDecl and m.body is None:
                    continue
                if m.name not in table:
                    c = Closure(node, env, m.name)
                    c.owner = tname
                    table[m.name] = [c]
        for e in d.embeds or []:
            self._install_defaults(tname, self.rtype_name(e), env)

    # ------------------------------------------------------------ misc declarations
    def ev_UsingDecl(self, n, env):
        v = yield from self.ev(n.expr, env)
        env.vars[n.name] = v
        if env.usings is None:
            env.usings = {}
        env.usings[n.name] = v
        return UNIT

    def ev_InitDecl(self, n, env):
        yield from self.ev_body(n.body, env)
        return UNIT

    def ev_TestDecl(self, n, env):
        self.tests.append((n.name, n.body, env))
        return Done(UNIT)

    def ev_ImportDecl(self, n, env):
        name = n.pkg[-1]
        pkg = self.load_package(n.pkg)
        if n.names:
            for nm in n.names:
                if nm in pkg.env.vars:
                    env.vars[nm] = pkg.env.vars[nm]
        else:
            env.vars[n.alias or name] = pkg
        return Done(UNIT)

    def load_package(self, parts):
        key = ".".join(parts)
        if key in self.packages:
            return self.packages[key]
        base = self.search_dir or "."
        cands = [os.path.join(base, *parts) + ".mxi", os.path.join(base, *parts, parts[-1] + ".mxi")]
        path = next((p for p in cands if os.path.exists(p)), None)
        if path is None:
            from .stdpkg import find_std
            path = find_std(parts)
            from .values import GC
            from .stdpkg import gc_only, refusal
            if gc_only(path, parts) and not GC[0]:
                raise Abort(refusal(parts))
        if path is None:
            raise Abort(f"cannot find package '{key}'")
        src = open(path, encoding="utf-8").read()
        prog = self.load_source(src, path)
        menv = self.new_module_env()
        self.mod_pkg[id(menv)] = key
        if path == cands[1]:                   # a package folder may carry its own Moxie.toml
            from .manifest import package_native
            self.pkg_native[key] = package_native(os.path.dirname(path))
        self.run_sync(self.exec_stmts(prog.stmts, menv))
        exp = self.exports.get(id(menv), set())
        pe = Env(None)
        pe.mod = pe
        for k in exp:
            if k in menv.vars:
                pe.vars[k] = menv.vars[k]
        pkg = PkgV(key, pe)
        self.packages[key] = pkg
        return pkg
