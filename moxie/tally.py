"""The compiler's pool tally, first version (Spec section 19).

For each kind of counted resource (the kinds `moxie --pools run` observes) this finds how many the program
creates, following calls: a function's count is its own creation sites plus the counts of the functions it
calls.  Sites are counted by name, like effects, so a method call counts every method of that name.

The closing rule: a resource that has an explicit close (files, sockets, listeners, connections, foreign
handles) and is bound to a name, then released in the same scope without being moved anywhere else, is *local*:
it is gone before the loop goes round again, so it counts once however often the loop runs.  A resource that
outlives its iteration or call (it is moved to a function other than its closer, returned, or created without a
name) is *kept*, and a kept resource created in a loop or in recursion cannot be sized, which is an error
(`problems`).  Atoms, channels, timers, and futures have no close, so they are always kept.

A count is *exact* when no creation is in a loop, a comprehension, a recursive function, or a fiber:
it is then a true upper bound on the number ever created, and so on the number open at once.  Otherwise it is
reported with a reason and a plus sign ("2+"): the tally knows a creation site but not how many times it runs,
and the observed run (`moxie --pools run`) says how many were open together.  Fiber code counts once per possible
live fiber: what a fiber function creates is multiplied by its limit (`fiber[n]`, else the manifest's
`[fibers] limit`), and the fibers it starts are counted from their own limits, not from its.  A fiber function with
no limit anywhere has an unknown multiplier, so its resources are reported with a plus sign and a warning.
"""
import os

from .ast import *   # noqa
from .effects import _children, _last

MAKERS = {"Atom": "Atom", "Cancel": "Cancel", "Timer": "Timer", "after": "Timer", "Future": "Future", "Chan": "Chan", "signals": "Chan", "watch": "Chan",
          "open_file": "Io file", "connect": "Io socket", "accept": "Io socket", "listen": "Listener",
          "connect_tls": "Io socket", "listen_tls": "Listener", "bind_udp": "Io socket",
          "connect_unix": "Io socket", "listen_unix": "Listener"}
LOOPS = (ForE, WhileE, CompE, ForM)


CLOSABLE = ("Io file", "Io socket", "Listener", "Connection")


def closable(kind):
    return kind in CLOSABLE or kind.startswith("handle ")


class Count:
    """kind -> [n, reasons, kept]; reasons is a set of 'loop' | 'recursion' | 'fiber'; kept says some
    resource of the kind outlives the code that created it."""
    def __init__(self):
        self.k = {}
        self.b = {}            # kind -> bytes of pool slots (layout.py), for the sites whose size is known
        self.why = []          # the sites whose size is not known, and what to write

    def add(self, kind, n=1, reasons=(), kept=True, nbytes=0, why=None):
        e = self.k.setdefault(kind, [0, set(), False])
        e[0] += n
        e[1] |= set(reasons)
        e[2] = e[2] or kept
        self.b[kind] = self.b.get(kind, 0) + nbytes
        if why and why not in self.why:
            self.why.append(why)

    def scale(self, m):
        for e in self.k.values():
            e[0] *= m
        for kind in self.b:
            self.b[kind] *= m

    def pool_bytes(self):
        """The bytes of all the pool slots, or None when some site's size is not known."""
        return None if self.why else sum(self.b.values())

    def merge(self, other, loop_reasons=(), fiber=False, release=False):
        """Add a callee's counts.  Loop and recursion reasons apply to what is kept; a fiber reason to all;
        `release` says the caller binds the callee's result and closes it itself."""
        for kind, (n, rs, kept) in other.k.items():
            if release and closable(kind):
                kept = False
            r = set(rs)
            if kept:
                r |= set(loop_reasons)
            if fiber:
                r.add("fiber")
            self.add(kind, n, r, kept)
        for kind, v in other.b.items():
            self.b[kind] = self.b.get(kind, 0) + v
        for w in other.why:
            if w not in self.why:
                self.why.append(w)


def names_in(n):
    """Every Name node under n (including n)."""
    out = []
    stack = [n]
    while stack:
        x = stack.pop()
        if x.__class__ is Name:
            out.append(x.name)
        for ch in _children(x):
            stack.append(ch)
    return out


def find_package(search_dir, parts):
    base = search_dir or "."
    cands = [os.path.join(base, *parts) + ".mxi", os.path.join(base, *parts, parts[-1] + ".mxi")]
    found = next((p for p in cands if os.path.exists(p)), None)
    if found is None:
        from .stdpkg import find_std
        found = find_std(parts)
    return found


def load_packages(prog, search_dir):
    """{package key: (path, source text, program)} for every package the program imports, directly or not."""
    from .parser import parse_program
    out = {}
    todo = [prog]
    while todo:
        cur = todo.pop(0)
        for st in cur.stmts:
            if st.__class__ is not ImportDecl:
                continue
            key = ".".join(st.pkg)
            if key in out:
                continue
            path = find_package(search_dir, st.pkg)
            if path is None:
                continue
            try:
                src = open(path, encoding="utf-8").read()
                pp = parse_program(src, path)
            except Exception:
                continue
            out[key] = (path, src, pp)
            todo.append(pp)
    return out


class Tally:
    def __init__(self, prog, default_limit=None, search_dir=None, _shared=None):
        self.prog = prog
        self.default_limit = default_limit
        self.search_dir = search_dir
        self.label = ""                # "" for the entry file, else the package key
        self._shared = _shared if _shared is not None else {}     # package key -> Tally, so a package is tallied once
        self.pkgs = {}                 # alias -> Tally of an imported package
        self.imported = {}             # name brought in by `import p (name)` -> (Tally, name)
        self.starts = {}             # function name -> set of fiber functions it starts with `run`
        self.start_sink = None
        self.defs = {}
        self.handle_fns = {}
        self.closers = {"close"}
        self.memo = {}
        self.stack = []
        self.cyclic = set()
        self.methods = set()         # names defined inside impl blocks, reachable as x.name(...) by UFCS
        self.problems = []           # (line, message): a kept resource created in a loop or recursion
        self._seen_problem = set()
        self._collect(prog)
        self._imports()

    def _imports(self):
        if self.search_dir is None:
            return
        from .parser import parse_program
        for st in self.prog.stmts:
            if st.__class__ is not ImportDecl:
                continue
            key = ".".join(st.pkg)
            sub = self._shared.get(key)
            if sub is None:
                path = find_package(self.search_dir, st.pkg)
                if path is None:
                    continue
                try:
                    pp = parse_program(open(path, encoding="utf-8").read(), path)
                except Exception:
                    continue
                sub = Tally.__new__(Tally)
                self._shared[key] = sub                    # registered first, so an import cycle cannot recurse
                sub.__init__(pp, self.default_limit, self.search_dir, self._shared)
                sub.label = key
                sub.path = path
            if st.names:
                for nm in st.names:
                    if isinstance(nm, str):
                        self.imported[nm] = (sub, nm)
            else:
                self.pkgs[st.alias or st.pkg[-1]] = sub

    def pk_methods(self, f):
        """Package methods an `x.name(...)` call can reach (UFCS): an impl method of the same name in any imported package."""
        if f.__class__ is GenApp:
            return self.pk_methods(f.base)
        if f.__class__ is not Field or (f.obj.__class__ is Name and f.obj.name in self.pkgs):
            return []
        subs = list(self.pkgs.values()) + [s for s, _n in self.imported.values()]
        seen, out = set(), []
        for s in subs:
            if id(s) not in seen and f.name in s.methods:
                seen.add(id(s))
                out.append((s, f.name))
        return out

    def pk(self, f):
        """(Tally, function name) when the callee `f` is a function of an imported package, else None."""
        c = f.__class__
        if c is GenApp:
            return self.pk(f.base)
        if c is Field and f.obj.__class__ is Name and f.obj.name in self.pkgs:
            sub = self.pkgs[f.obj.name]
            return (sub, f.name) if f.name in sub.defs else None
        if c is Name and f.name in self.imported and f.name not in self.defs:
            sub, orig = self.imported[f.name]
            return (sub, orig) if orig in sub.defs else None
        return None

    def _collect(self, n, in_impl=False):
        c = n.__class__
        if c is ForeignDecl:
            hn = {h[0] for h in n.handles or []}
            for h in n.handles or []:
                if len(h) > 1 and h[1]:
                    self.closers.add(h[1])
            for d in n.fns:
                r = d.ret
                t = _last(r) if r is not None and r.__class__ is TName else None
                if t == "Result" and r.groups and r.groups[0]:
                    t = _last(r.groups[0][0])
                if t in hn:
                    self.handle_fns[d.name] = "handle " + t
        elif c is FnDecl and n.name and n.body is not None:
            self.defs.setdefault(n.name, []).append(n)
            if in_impl:
                self.methods.add(n.name)
        for ch in _children(n):
            self._collect(ch, in_impl or c is ImplDecl)

    # ---------------------------------------------------------------- one function
    def of_fn(self, name):
        if name in self.memo:
            return self.memo[name]
        if name in self.stack:
            self.cyclic.update(self.stack[self.stack.index(name):])
            return Count()
        self.stack.append(name)
        total = Count()
        saved, self.start_sink = self.start_sink, set()
        for d in self.defs.get(name, []):
            total.merge(self.body(d.body, d.body))
            if d.guard is not None:
                total.merge(self.body(d.guard, d.body))
        self.starts[name] = self.start_sink
        if saved is not None:
            saved |= self.start_sink              # what a called function starts, its caller starts too
        self.start_sink = saved
        self.stack.pop()
        if name in self.cyclic:
            for kind, e in total.k.items():
                if e[2]:
                    e[1].add("recursion")
                    self.problem(self.defs[name][0].line, f"'{name}' is recursive and creates a {kind} that outlives the call, so the number of {kind} cannot be counted")
        self.memo[name] = total
        return total

    def problem(self, line, msg):
        if (line, msg) not in self._seen_problem:
            self._seen_problem.add((line, msg))
            self.problems.append((line, msg))

    # ---------------------------------------------------------------- a body
    def body(self, n, fnscope):
        out = Count()
        self.walk(n, (), False, out, fnscope)
        return out

    def escapes(self, v, scope, fnscope=None):
        """Does the resource bound to `v` leave `scope` other than by being closed?"""
        found = [False]

        def visit(n, parent):
            if found[0] or n is None:
                return
            c = n.__class__
            if c is Call:
                callee = n.fn.name if n.fn.__class__ is Name else (n.fn.name if n.fn.__class__ is Field else None)
                for a in n.args:
                    e = a.expr
                    moved = a.mod == "move" or e.__class__ is Move
                    inner = e.e if e.__class__ is Move else e
                    if inner.__class__ is Name and inner.name == v and moved and callee not in self.closers:
                        found[0] = True
                        return
            elif c is Move and n.e.__class__ is Name and n.e.name == v and parent.__class__ is not Arg:
                found[0] = True
                return
            elif c is Return and n.e is not None and v in names_in(n.e):
                found[0] = True
                return
            elif c is Lambda and v in names_in(n.body):
                found[0] = True              # captured by a closure
                return
            for ch in _children(n):
                visit(ch, n)
        visit(scope, None)
        if found[0]:
            return True
        # the tail expression of the scope is its value
        tail = scope
        while tail.__class__ is Block and tail.stmts:
            tail = tail.stmts[-1]
        is_closer = tail.__class__ is Call and (tail.fn.name if tail.fn.__class__ is Name else None) in self.closers
        if scope is fnscope and tail is not scope and tail.__class__ is not Assign and not is_closer and v in names_in(tail):
            return True
        return False

    def walk(self, n, loops, in_fiber, out, fnscope):
        if n is None:
            return
        c = n.__class__
        if c is FnDecl or c is FnGroup:
            return
        scope = loops[-1] if loops else fnscope
        in_loop = bool(loops)
        if c is Lambda:
            self.walk(n.body, loops + (n.body,), in_fiber, out, fnscope)      # a lambda may run any number of times
            return
        fiber = in_fiber
        if c is RunE:
            tgt = n.target
            if tgt.__class__ is Call:
                for a in tgt.args:
                    self.walk(a.expr, loops, in_fiber, out, fnscope)
                nm = tgt.fn.name if tgt.fn.__class__ is Name else None
                own = self.pk(tgt.fn)
                if own is not None:
                    if self.start_sink is not None:
                        self.start_sink.add(own)
                elif nm in self.defs:
                    if self.start_sink is not None:
                        self.start_sink.add((self, nm))
            elif tgt.__class__ is Lambda:
                self.walk(tgt.body, loops, True, out, fnscope)          # an unnamed fiber has no limit
            return
        if c is Assign and n.targets.__class__ is PBind:
            v = n.targets.name
            val = n.value
            while val.__class__ in (Q, Move):
                val = val.e
            if val.__class__ is Call:
                nm, kind = self.callee(val.fn)
                own = self.pk(val.fn)
                local = not self.escapes(v, scope, fnscope)
                if kind is not None and closable(kind) and own is None:
                    self.site(out, kind, val, in_loop, fiber, kept=not local)
                    self.args(val, loops, fiber, out, fnscope)
                    return
                if own is not None and local:
                    self.call_in(out, own[1], val, in_loop, fiber, release=True, owner=own[0])
                    self.args(val, loops, fiber, out, fnscope)
                    return
                if own is None and nm in self.defs and local:
                    self.call_in(out, nm, val, in_loop, fiber, release=True)
                    self.args(val, loops, fiber, out, fnscope)
                    return
        if c is Call:
            nm, kind = self.callee(n.fn)
            own = self.pk(n.fn)
            if own is not None:
                self.call_in(out, own[1], n, in_loop, fiber, owner=own[0])
            elif kind is not None:
                self.site(out, kind, n, in_loop, fiber, kept=True)
            elif nm in self.defs:
                self.call_in(out, nm, n, in_loop, fiber)
            for sub, mn in self.pk_methods(n.fn):
                self.call_in(out, mn, n, in_loop, fiber, owner=sub)
            if n.fn.__class__ is not Name and n.fn.__class__ is not GenApp:
                self.walk(n.fn, loops, in_fiber, out, fnscope)
            self.args(n, loops, fiber, out, fnscope)
            return
        if c is Pipe:
            self.walk(n.l, loops, in_fiber, out, fnscope)
            st = n.stage
            nm = st.fn.name if st.__class__ is Call and st.fn.__class__ is Name else (st.name if st.__class__ is Name else None)
            own = self.pk(st.fn if st.__class__ is Call else st)
            if own is not None:
                self.call_in(out, own[1], st, in_loop, fiber, owner=own[0])
            elif nm in self.defs:
                self.call_in(out, nm, st, in_loop, fiber)
            self.walk(st, loops, in_fiber, out, fnscope)
            return
        if c in LOOPS or c is DaemonE:
            body = n.body if hasattr(n, "body") and n.body is not None else n
            inner = loops + (body,)
            for ch in _children(n):
                self.walk(ch, inner, in_fiber, out, fnscope)
            return
        for ch in _children(n):
            self.walk(ch, loops, in_fiber, out, fnscope)

    def args(self, call, loops, fiber, out, fnscope):
        for a in call.args:
            self.walk(a.expr, loops, fiber, out, fnscope)
        if call.trailing is not None:
            self.walk(call.trailing, loops, fiber, out, fnscope)

    def site(self, out, kind, call, in_loop, fiber, kept):
        reasons = set()
        if in_loop and kept:
            reasons.add("loop")
            self.problem(call.line, f"a {kind} is created in a loop and outlives the iteration, so the number of {kind} cannot be counted "
                                    "(close it in the same iteration, or create it before the loop)")
        if fiber:
            reasons.add("fiber")
        from .layout import slot_bytes, type_decls
        if getattr(self, "decls", None) is None:
            self.decls = type_decls(self.prog)
        nb, why = slot_bytes(kind, call, self.decls)
        where = (self.label + ": " if self.label else "") + f"line {call.line}: "
        out.add(kind, 1, reasons, kept, nb or 0, None if nb is not None else where + why)

    def call_in(self, out, nm, call, in_loop, fiber, release=False, owner=None):
        owner = owner or self
        callee = owner.of_fn(nm)
        if owner is not self and self.start_sink is not None:
            self.start_sink |= {x for x in owner.starts.get(nm, ())}
        for kind, (n, rs, kept) in callee.k.items():
            if release and closable(kind):
                kept = False
            if in_loop and kept:
                self.problem(call.line, f"'{(owner.label + '.') if owner is not self else ''}{nm}' creates a {kind} that outlives the call, and it is called in a loop, so the number of {kind} cannot be counted")
        out.merge(callee, loop_reasons=("loop",) if in_loop else (), fiber=fiber, release=release)

    def callee(self, f):
        """(name, creation kind or None) for the function expression of a call."""
        c = f.__class__
        if c is GenApp:
            return self.callee(f.base)
        if c is Name:
            if f.name in self.defs:
                return f.name, None
            if f.name in self.handle_fns:
                return f.name, self.handle_fns[f.name]
            return f.name, MAKERS.get(f.name)
        if c is Field and f.obj.__class__ is Name and f.obj.name == "Connection" and f.name in ("open", "memory"):
            return None, "Connection"
        if c is Field:
            return f.name, None
        return None, None

    def limit_of(self, name):
        for d in self.defs.get(name, []):
            for fl in d.flags or ():
                if isinstance(fl, str) and fl.startswith("fiber:"):
                    return int(fl[6:])
        return self.default_limit

    def _top(self):
        """(counts, fiber functions started) for the file's own top-level statements."""
        top = Count()
        saved, self.start_sink = self.start_sink, set()
        scope = Block([s for s in self.prog.stmts if s.__class__ not in (FnDecl, FnGroup)])
        for st in self.prog.stmts:
            if st.__class__ not in (FnDecl, FnGroup, TupleDecl, EnumDecl, IfaceDecl, ImplDecl, AliasDecl, ForeignDecl, ImportDecl):
                top.merge(self.body(st, scope))
        started, self.start_sink = self.start_sink, saved
        return top, started

    def program(self):
        top, started = self._top()
        for sub in self._shared.values():            # an imported package runs its top level when it is imported
            c2, s2 = sub._top()
            top.merge(c2)
            started |= s2
        todo, seen = list(started), []
        while todo:
            item = todo.pop()
            if item in seen:
                continue
            seen.append(item)
            own, f = item
            cnt = own.of_fn(f)
            lim = own.limit_of(f)
            part = Count()
            part.merge(cnt)
            if lim is not None:
                part.scale(lim)
                top.merge(part)
            else:
                top.merge(part, fiber=True)
                if cnt.k:
                    nm = (own.label + "." if own.label else "") + f
                    self.warnings.append(f"fiber function '{nm}' creates resources but has no limit: write fiber[n] or set [fibers] limit in Moxie.toml")
            todo.extend(own.starts.get(f, ()))
        self.fibers = [((own.label + "." if own.label else "") + f, own.limit_of(f)) for own, f in seen]
        lines = {".".join(st.pkg): st.line for st in self.prog.stmts if st.__class__ is ImportDecl}
        for key, sub in self._shared.items():
            for line, msg in sub.problems:
                self.problem(lines.get(key, 1), f"in package '{key}' ({os.path.basename(sub.path)}:{line}): {msg}")
        return top

    @property
    def warnings(self):
        return self.__dict__.setdefault("_warnings", [])

    def fiber_count(self):
        """(largest possible number of fibers, exact?): the entry fiber plus every fiber function's limit."""
        if any(l is None for _f, l in self.fibers):
            return 1 + sum(l for _f, l in self.fibers if l is not None), False
        return 1 + sum(l for _f, l in self.fibers), True


def static_tally(prog, default_limit=None, search_dir=None):
    return Tally(prog, default_limit, search_dir).program()


def tally_problems(prog, search_dir=None):
    t = Tally(prog, None, search_dir)
    t.program()
    return t.problems


def program_hash(src, search_dir=None, prog=None):
    """A hash of the program's tokens and those of every package it imports: layout, spacing, and comments do not
    change it, so `moxie fmt` leaves a header valid, and a change in a package makes it stale."""
    import hashlib
    from .fmt import _tokens

    def toks(text, name):
        try:
            return "\n".join(f"{k} {v}" for k, v in _tokens(text, name) if k not in ("NL", "INDENT", "DEDENT", "EOF"))
        except Exception:
            return "text:" + text
    parts = ["tokens:" + toks(src, "<program>")]
    if prog is not None and search_dir is not None:
        for key, (path, text, _p) in sorted(load_packages(prog, search_dir).items()):
            parts.append(f"package {key}:" + toks(text, path))
    return hashlib.sha256("\n--\n".join(parts).encode("utf-8")).hexdigest()


def header_dict(t, cnt, src=None):
    """The pool header: what the runtime needs to size the pools and the fiber blocks before the first line runs."""
    n, exact = t.fiber_count()
    pools = {k: (e[0] if not e[1] else None) for k, e in sorted(cnt.k.items())}
    d = {"version": 1, "pools": pools, "fibers": {"largest": n if exact else None, "functions": dict(t.fibers)},
         "exact": exact and all(v is not None for v in pools.values()),
         "bytes": {"pools": cnt.pool_bytes(), "unknown": list(cnt.why)}}
    if src is not None:
        d["program"] = program_hash(src, t.search_dir, t.prog)
    return d


def format_header(t, cnt, src=None):
    import json
    return json.dumps(header_dict(t, cnt, src), indent=2) + "\n"


def format_fibers(t):
    n, exact = t.fiber_count()
    lines = []
    if t.fibers:
        lines.append("fibers: entry, " + ", ".join(f"{f} (limit {l if l is not None else 'none'})" for f, l in t.fibers))
    lines.append(f"largest possible fiber count: {n}{'' if exact else '+ (a fiber function has no limit)'}")
    return "\n".join(lines) + "\n"


def format_tally(cnt):
    if not cnt.k:
        return "pool tally (static): no counted resource is created\n"
    w = max(len(k) for k in cnt.k)
    out = ["pool tally (static): kind, creation sites reached, note"]
    for k in sorted(cnt.k):
        n, rs, kept = cnt.k[k]
        note = ""
        if rs:
            why = {"loop": "created in a loop and kept", "recursion": "created in recursion and kept", "fiber": "created in a fiber function with no limit"}
            note = "  " + "; ".join(why[r] for r in sorted(rs))
        out.append(f"  {k.ljust(w)}  {str(n) + ('+' if rs else ''):>4}{note}")
    out.append("  (N is the number of creation sites reached through calls; N+ means a site runs an unknown number of times,")
    out.append("   so `moxie --pools run` is the evidence for how many are open together)")
    pb = cnt.pool_bytes()
    if pb is not None:
        out.append(f"  pool memory: {pb} bytes (slot sizes from layout.py)")
    else:
        out.append("  pool memory: not known; " + "; ".join(cnt.why[:3]))
    return "\n".join(out) + "\n"


def compare(cnt, pools):
    """Lines that warn where the observed use is above an exact static count (a bug in the tally)."""
    lines = []
    for kind, peak in sorted(pools.peak.items()):
        n, rs, kept = cnt.k.get(kind, [0, set(), False])
        if not rs and peak > n:
            lines.append(f"warning: observed {peak} open {kind} at once, but the static tally says {n}")
    return lines
