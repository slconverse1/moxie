"""The compiler's pool tally, first version (Spec section 19).

For each kind of counted resource (the kinds `moxie --pools run` observes) this finds how many the program
creates, following calls: a function's count is its own creation sites plus the counts of the functions it
calls.  Sites are counted by name, like effects, so a method call counts every method of that name.

A count is *exact* when no creation is in a loop, a comprehension, a recursive function, or a fiber:
it is then a true upper bound on the number ever created, and so on the number open at once.  Otherwise it is
reported with a reason and a plus sign ("2+"): the tally knows a creation site but not how many times it runs,
and the observed run (`moxie --pools run`) says how many were open together.  Fiber code counts once per possible
live fiber, so a creation reached from `run` is reported as a multiple.
"""
from .ast import *   # noqa
from .effects import _children, _last

MAKERS = {"Atom": "Atom", "Timer": "Timer", "after": "Timer", "Future": "Future", "Chan": "Chan",
          "open_file": "Io file", "connect": "Io socket", "accept": "Io socket", "listen": "Listener"}
LOOPS = (ForE, WhileE, CompE, ForM)


class Count:
    """kind -> [n, reasons]; reasons is a set of 'loop' | 'recursion' | 'fiber'."""
    def __init__(self):
        self.k = {}

    def add(self, kind, n=1, reasons=()):
        e = self.k.setdefault(kind, [0, set()])
        e[0] += n
        e[1] |= set(reasons)

    def merge(self, other, reasons=()):
        for kind, (n, rs) in other.k.items():
            self.add(kind, n, set(rs) | set(reasons))


class Tally:
    def __init__(self, prog):
        self.prog = prog
        self.defs = {}
        self.handle_fns = {}
        self.memo = {}
        self.stack = []
        self.cyclic = set()
        self._collect(prog)

    def _collect(self, n):
        c = n.__class__
        if c is ForeignDecl:
            hn = {h[0] for h in n.handles or []}
            for d in n.fns:
                r = d.ret
                t = _last(r) if r is not None and r.__class__ is TName else None
                if t == "Result" and r.groups and r.groups[0]:
                    t = _last(r.groups[0][0])
                if t in hn:
                    self.handle_fns[d.name] = "handle " + t
        elif c is FnDecl and n.name and n.body is not None:
            self.defs.setdefault(n.name, []).append(n)
        for ch in _children(n):
            self._collect(ch)

    # ---------------------------------------------------------------- one function
    def of_fn(self, name):
        if name in self.memo:
            return self.memo[name]
        if name in self.stack:
            self.cyclic.update(self.stack[self.stack.index(name):])
            return Count()
        self.stack.append(name)
        total = Count()
        for d in self.defs.get(name, []):
            total.merge(self.body(d.body, False, False))
            if d.guard is not None:
                total.merge(self.body(d.guard, False, False))
        self.stack.pop()
        if name in self.cyclic:
            for kind, e in total.k.items():
                e[1].add("recursion")
        self.memo[name] = total
        return total

    # ---------------------------------------------------------------- a body
    def body(self, n, in_loop, in_fiber):
        out = Count()
        self.walk(n, in_loop, in_fiber, out)
        return out

    def walk(self, n, in_loop, in_fiber, out):
        if n is None:
            return
        c = n.__class__
        if c is FnDecl or c is FnGroup:
            return
        if c is Lambda:
            self.walk(n.body, in_loop, in_fiber, out)      # a lambda may run any number of times
            return
        reasons = set()
        if in_loop:
            reasons.add("loop")
        if in_fiber:
            reasons.add("fiber")
        if c is RunE:
            tgt = n.target
            if tgt.__class__ is Call:
                for a in tgt.args:
                    self.walk(a.expr, in_loop, in_fiber, out)
                nm = tgt.fn.name if tgt.fn.__class__ is Name else None
                if nm in self.defs:
                    out.merge(self.of_fn(nm), set(reasons) | {"fiber"})
            return
        if c is Call:
            nm, kind = self.callee(n.fn)
            if kind is not None:
                out.add(kind, 1, reasons)
            elif nm in self.defs:
                out.merge(self.of_fn(nm), reasons)
            if n.fn.__class__ is not Name and n.fn.__class__ is not GenApp:
                self.walk(n.fn, in_loop, in_fiber, out)
            for a in n.args:
                self.walk(a.expr, in_loop, in_fiber, out)
            if n.trailing is not None:
                self.walk(n.trailing, in_loop, in_fiber, out)
            return
        if c is Pipe:
            self.walk(n.l, in_loop, in_fiber, out)
            st = n.stage
            nm = st.fn.name if st.__class__ is Call and st.fn.__class__ is Name else (st.name if st.__class__ is Name else None)
            if nm in self.defs:
                out.merge(self.of_fn(nm), reasons)
            self.walk(st, in_loop, in_fiber, out)
            return
        loop = in_loop or c in LOOPS
        if c is DaemonE:
            loop = True                      # a daemon body repeats
        for ch in _children(n):
            self.walk(ch, loop, in_fiber, out)

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

    def program(self):
        top = Count()
        for st in self.prog.stmts:
            if st.__class__ not in (FnDecl, FnGroup, TupleDecl, EnumDecl, IfaceDecl, ImplDecl, AliasDecl, ForeignDecl):
                top.merge(self.body(st, False, False))
        return top


def static_tally(prog):
    return Tally(prog).program()


def format_tally(cnt):
    if not cnt.k:
        return "pool tally (static): no counted resource is created\n"
    w = max(len(k) for k in cnt.k)
    out = ["pool tally (static): kind, creation sites reached, note"]
    for k in sorted(cnt.k):
        n, rs = cnt.k[k]
        note = ""
        if rs:
            why = {"loop": "created in a loop", "recursion": "created in recursion", "fiber": "created in fiber code (once per live fiber)"}
            note = "  " + "; ".join(why[r] for r in sorted(rs))
        out.append(f"  {k.ljust(w)}  {str(n) + ('+' if rs else ''):>4}{note}")
    out.append("  (N is the number of creation sites reached through calls; N+ means a site runs an unknown number of times,")
    out.append("   so `moxie --pools run` is the evidence for how many are open together)")
    return "\n".join(out) + "\n"


def compare(cnt, pools):
    """Lines that warn where the observed use is above an exact static count (a bug in the tally)."""
    lines = []
    for kind, peak in sorted(pools.peak.items()):
        k = kind
        n, rs = cnt.k.get(k, [0, set()])
        if not rs and peak > n:
            lines.append(f"warning: observed {peak} open {kind} at once, but the static tally says {n}")
    return lines
