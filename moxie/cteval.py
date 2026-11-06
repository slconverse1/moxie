"""Compile-time evaluation (Spec section 14): the checker runs a pure function of the program on constant arguments in a sandboxed
interpreter (no permissions, output discarded) with a step limit.  Used where a constant is needed: a size, a type-level number,
a guard, and a top-level constant binding.  The result is a Python int, float, bool or str, or the call is not evaluated."""
import io

DEFAULT_FUEL = 200000


class FuelOut(Exception):
    pass


class CtEval:
    def __init__(self, prog, search_dir=None, fuel=None):
        self.prog = prog
        self.search_dir = search_dir
        self.fuel = fuel or DEFAULT_FUEL
        self.I = None
        self.env = None
        self.ok = None                 # None: not set up yet; False: cannot be used
        self.pure = set()
        self.cache = {}
        self.errors = []               # (line, message)
        self.warnings = []             # a call that always gives an Err
        self.left = 0

    def setup(self):
        if self.ok is not None:
            return self.ok
        self.ok = False
        try:
            from .effects import Effects
            from .interp import Interp
            from .perms import Perms
            ef = Effects(self.prog, self.search_dir)
            ef.solve()
            decls = {}
            for st in self.prog.stmts:
                if st.__class__.__name__ in ("FnDecl", "FnGroup"):
                    nm = getattr(st, "name", None)
                    decls.setdefault(nm, []).append(st)
            for nm, ds in decls.items():
                s = ef.sum.get(nm)
                if s is not None and not s.eff and all("impure" not in (d.flags or ()) for d in ds):
                    self.pure.add(nm)
            self.ef = ef
            for nm, (sub, orig) in ef.imported.items():                  # `import mathx (big)`: big
                if nm not in ef.defs and self._pkg_pure(sub, orig):
                    self.pure.add(nm)
            for alias, sub in ef.pkgs.items():                           # `import mathx`: mathx.big
                for orig in sub.defs:
                    if self._pkg_pure(sub, orig):
                        self.pure.add(f"{alias}.{orig}")
            I = Interp(out=io.StringIO(), err=io.StringIO(), search_dir=self.search_dir)
            I.perms = Perms.none()
            env = I.new_module_env()
            I.module_env = env
            I.main_prog = self.prog
            keep = [st for st in self.prog.stmts
                    if st.__class__.__name__ in ("FnDecl", "FnGroup", "TupleDecl", "EnumDecl", "AliasDecl", "IfaceDecl", "ImplDecl",
                                                 "ImportDecl")]

            def body():
                return (yield from I.exec_stmts(keep, env))
            I.sched.run_main(body())
            self.I, self.env = I, env
            self._meter(I)
            self.ok = True
        except Exception:
            self.ok = False
        return self.ok

    def _meter(self, I):
        """Count every evaluation step; stop the run when the limit is spent."""
        outer = self

        def wrap(f):
            def counted(n, env):
                outer.left -= 1
                if outer.left < 0:
                    raise FuelOut()
                return f(n, env)
            return counted
        I.disp = {k: wrap(v) for k, v in I.disp.items()}

    @staticmethod
    def _pkg_pure(sub, orig):
        s = sub.sum.get(orig)
        return s is not None and not s.eff and all("impure" not in (d.flags or ()) for d in sub.defs.get(orig, ()))

    def key_of(self, fn):
        """The name a call is known by (`big`, or `mathx.big` for a function of an imported package) when it is a pure function the
        compiler can run, else None."""
        c = fn.__class__.__name__
        if c == "Name":
            key = fn.name
        elif c == "Field" and fn.obj.__class__.__name__ == "Name":
            key = f"{fn.obj.name}.{fn.name}"
        else:
            return None
        return key if self.can_call(key) else None

    def can_call(self, name):
        return self.setup() and name in self.pure

    def call(self, name, args, line=0):
        """The value of `name(*args)`, or None when it cannot be evaluated here (an abort or the step limit is recorded as an error)."""
        key = (name, tuple(args), line)
        if key in self.cache:
            return self.cache[key]
        self.cache[key] = None
        if not self.can_call(name):
            return None
        I = self.I
        self.left = self.fuel
        I.err = io.StringIO()
        from .ast import Name, Field
        node = Field(Name(name.split(".")[0], line=0), name.split(".")[1], line=0) if "." in name else Name(name, line=0)

        def go():
            f = yield from I.ev(node, self.env)
            return (yield from I.apply(f, list(args)))
        try:
            v = I.sched.run_main(go())
        except BaseException as e:
            if isinstance(e, RecursionError):
                self.errors.append((line, f"`{name}` recursed too deeply while the compiler was evaluating it"))
                return None
            if self.left < 0:
                self.errors.append((line, f"`{name}` did not finish in {self.fuel} steps while the compiler was evaluating it "
                                          f"(`eval_fuel` in [program] changes the limit)"))
                return None
            msg = I.err.getvalue().strip()
            if not msg and isinstance(e, BaseException) and getattr(e, "msg", None):
                msg = "x: " + str(e.msg)
            if msg:
                msg = msg.split(":", 1)[1].strip() if ":" in msg else msg
                self.errors.append((line, f"evaluating `{name}({', '.join(map(_show, args))})` at compile time aborts: {msg}"))
            return None
        if v.__class__.__name__ == "EnumV" and v.case == "Err":
            from .core import show as show_value
            try:
                shown = show_value(v, I)
            except Exception:
                shown = "Err(...)"
            self.warnings.append((line, f"`{name}({', '.join(map(_show, args))})` always gives `{shown}`: the compiler worked it out with constant arguments"))
            return None
        if isinstance(v, (int, float, bool, str)):
            self.cache[key] = (v,)
            return (v,)
        return None


def _show(v):
    return '"%s"' % v if isinstance(v, str) else (str(v).lower() if isinstance(v, bool) else str(v))
