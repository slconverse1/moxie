"""`moxie repl`: type an expression or a declaration and see the result.

Each accepted input joins the session, so later inputs see earlier bindings, functions, types, and imports.  Before an input
runs, the whole session plus the new input is checked, and a compile error leaves the session as it was.  Only the new input
runs, in the session's one module scope, so earlier side effects do not repeat.

A bare expression is bound to `res1`, `res2`, ... (ordinary names, no special syntax), and `it` is always the latest one.
A unit result (`println(...)`) is not bound.  Commands: `:type expr`, `:reset`, `:results`, `:help`, `:quit`.
"""
import sys
from .lexer import MoxieSyntaxError
from .parser import parse_program
from .ast import ExprStmt, Assign, PBind
from .check import Checker, tshow
from .core import show
from .values import UNIT, Abort
from .core import ProgramExit

HELP = """moxie repl
  an expression    prints its value and type, and binds it to res1, res2, ... (and `it` for the latest)
  a declaration    fn, tuple, enum, impl, import, or `name = value` joins the session
  a block          a line ending in `:` or `->` continues until a blank line
  :type expr       the type of an expression, without running it
  :results         every resN with its type and value
  :reset           forget the session
  :quit            leave (or end of input)
"""


class Session:
    def __init__(self, I, out, err):
        self.I, self.out, self.err = I, out, err
        self.reset()

    def reset(self):
        self.chunks = []          # accepted source, in order, for checking
        self.n = 0                # how many results so far
        self.results = []         # (name, type text, value text)
        self.I.module_env = self.env = self.I.new_module_env()

    # ------------------------------------------------------------ checking
    def check(self, src):
        """(diagnostics, checker) for the session plus `src`; a syntax error is raised."""
        text = "\n".join(self.chunks + [src]) + "\n"
        prog = parse_program(text, "<repl>")
        from .check import check_program
        diags = self.I.static_check(prog)
        ck = Checker(set(self.I.prelude.vars))
        ck.search_dir = self.I.search_dir
        try:
            from .check import CT
            from .cteval import CtEval
            CT[0] = CtEval(prog, self.I.search_dir, None)
            ck.check(prog)
        except Exception:
            ck = None
        finally:
            from .check import CT
            CT[0] = None
        return diags, ck

    def type_of(self, name, ck):
        v = ck.top.vars.get(name) if ck is not None and getattr(ck, "top", None) is not None else None
        return tshow(v.ty) if v is not None and v.ty is not None else "?"

    # ------------------------------------------------------------ one input
    def feed(self, text):
        text = text.strip("\n")
        if not text.strip():
            return
        if text.lstrip().startswith(":"):
            return self.command(text.strip())
        try:
            stmts = parse_program(text, "<repl>").stmts
        except MoxieSyntaxError as e:
            self.err.write(f"error: {e.msg}\n")
            return
        bare = len(stmts) == 1 and stmts[0].__class__ is ExprStmt
        name = None
        src = text
        if bare:
            name = f"res{self.n + 1}"
            src = f"{name} = {text}"
        try:
            diags, ck = self.check(src)
        except MoxieSyntaxError as e:
            self.err.write(f"error: {e.msg}\n")
            return
        errs = [d for d in diags if d.kind == "error"]
        if len(errs) > 1:
            errs = [d for d in errs if not d.msg.startswith("evaluating ")] or errs     # the compile-time run repeats an error already shown
        for d in diags:
            if d.kind == "warning" and getattr(d, "unverified", True):
                self.err.write(f"warning: {d.msg}\n")
        if errs:
            for d in errs:
                self.err.write(f"error: {d.msg}\n")
            return
        new = parse_program(src, "<repl>").stmts
        try:
            self.I.sched.run_main(self.I.exec_stmts(new, self.env))
        except ProgramExit as e:
            if e.msg and not getattr(e, "printed", False):
                self.err.write(e.msg + "\n")
            return
        except Abort as a:
            self.err.write(f"abort: {a.msg}\n")
            return
        self.out.flush() if hasattr(self.out, "flush") else None
        self.chunks.append(src)
        if name is not None:
            val = self.env.vars.get(name)
            if val is UNIT:
                self.chunks.pop()                 # a unit result is not kept
                self.env.vars.pop(name, None)
                return
            self.n += 1
            ty = self.type_of(name, ck)
            vt = show(val, self.I)
            self.results.append((name, ty, vt))
            self.out.write(f"{name}: {ty} = {vt}\n")
            self.chunks.append(f"it = {name}")
            self.env.vars["it"] = val
        else:
            for st in new:
                if st.__class__ is Assign and not isinstance(st.targets, list) and st.targets.__class__ is PBind:
                    nm = st.targets.name
                    val = self.env.vars.get(nm)
                    self.out.write(f"{nm}: {self.type_of(nm, ck)} = {show(val, self.I)}\n")

    # ------------------------------------------------------------ commands
    def command(self, line):
        word, _, rest = line.partition(" ")
        if word in (":quit", ":q", ":exit"):
            raise EOFError
        if word == ":help":
            self.out.write(HELP)
        elif word == ":reset":
            self.reset()
            self.out.write("session cleared\n")
        elif word == ":results":
            for name, ty, vt in self.results:
                self.out.write(f"{name}: {ty} = {vt}\n")
        elif word == ":type":
            if not rest.strip():
                self.err.write("error: write an expression after :type\n")
                return
            try:
                diags, ck = self.check(f"__t = {rest.strip()}")
            except MoxieSyntaxError as e:
                self.err.write(f"error: {e.msg}\n")
                return
            errs = [d for d in diags if d.kind == "error"]
            if len(errs) > 1:
                errs = [d for d in errs if not d.msg.startswith("evaluating ")] or errs
            if errs:
                for d in errs:
                    self.err.write(f"error: {d.msg}\n")
                return
            self.out.write(f"{self.type_of('__t', ck)}\n")
        else:
            self.err.write(f"error: unknown command {word} (try :help)\n")


def needs_more(text):
    """True while the input is unfinished: it ends in `:` or `->`, a backslash, or has an open bracket."""
    t = text.rstrip()
    if t.endswith((":", "->", "\\")):
        return True
    depth = 0
    in_str = False
    prev = ""
    for c in t:
        if c == '"' and prev != "\\":
            in_str = not in_str
        elif not in_str:
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
        prev = c
    return depth > 0


def main(args, I):
    out, err = sys.stdout, sys.stderr
    tty = sys.stdin.isatty()
    s = Session(I, out, err)
    if tty:
        out.write("moxie repl  (:help for commands, :quit to leave)\n")
    buf = []
    while True:
        try:
            prompt = ("  ...> " if buf else "moxie> ") if tty else ""
            if tty:
                out.write(prompt)
                out.flush()
            line = sys.stdin.readline()
            if line == "":
                if buf:
                    s.feed("\n".join(buf))
                return 0
            line = line.rstrip("\n")
            if buf:
                if line.strip() == "":
                    s.feed("\n".join(buf))
                    buf = []
                else:
                    buf.append(line)
                continue
            if needs_more(line):
                buf = [line]
                continue
            s.feed(line)
            out.flush()
            err.flush()
        except EOFError:
            return 0
        except KeyboardInterrupt:
            buf = []
            out.write("\n")
