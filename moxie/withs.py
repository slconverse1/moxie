"""`do with Figure:` opens the case names of an enum for a block: inside it `Circle(r: 2.0)` and the pattern `Rect(w, h)` mean
`Figure.Circle(r: 2.0)` and `Figure.Rect(w, h)`.  `do with A, B:` opens several.  The block is rewritten to a `do:` block with the
qualified names written out, so the checker and the interpreter never see a `with`."""
from .ast import *   # noqa
from .lexer import MoxieSyntaxError

PRELUDE_ENUMS = {"Option": ["Some", "None"]}            # the prelude's enums whose cases are bare names already
UNUSED = {}          # id of a rewritten `do with` block -> the enums it names but never uses (the checker warns, see `e_DoE`)


def expand_withs(stmts, file="<input>", strict=False, scope=None):
    """Rewrite every `with` block whose enums are all known here.  A block naming an enum declared elsewhere (another file of the
    package) is left for a later call; with `strict` it is an error.  `scope` is the statements that declare the enums when they
    are more than `stmts` (all the files of a package)."""
    if not _has_with(stmts):
        return stmts
    enums, others = {}, set()
    for s in (scope if scope is not None else stmts):
        c = s.__class__
        if c is EnumDecl:
            enums[s.name] = [cs.name for cs in s.cases or []]
        elif c is TupleDecl or c is FnDecl or c is AliasDecl:
            others.add(s.name)
        elif c is FnGroup:
            others.add(getattr(s, "name", None))
    for k, v in PRELUDE_ENUMS.items():
        enums.setdefault(k, v)

    used = set()          # (enum, id of the `with` that opened it) for every case written bare inside a block

    def fail(line, msg):
        raise MoxieSyntaxError(msg, line, 0, file)

    def make_env(w):
        env = {}
        for e in w.enums:
            if e not in enums:
                if strict:
                    fail(w.line, f"`with {e}:` names no enum that is declared here")
                return None
            for cn in enums[e]:
                if cn in env and env[cn][0] != e:
                    fail(w.line, f"`{cn}` is a case of both `{env[cn][0]}` and `{e}`: write it as `{env[cn][0]}.{cn}` or `{e}.{cn}` in this block")
                if cn in others:
                    fail(w.line, f"`{cn}` is a case of `{e}` and also the name of a function or type: rename one, or write `{e}.{cn}`")
                env[cn] = (e, id(w))
        return env

    def rw(x, env):
        if isinstance(x, list):
            return [rw(i, env) for i in x]
        if isinstance(x, tuple):
            return tuple(rw(i, env) for i in x)
        if not isinstance(x, N):
            return x
        c = x.__class__
        if c is WithE:
            inner = make_env(x)
            if inner is None:
                x.body = rw(x.body, env)
                return x
            merged = dict(env or {})
            merged.update(inner)
            body = rw(x.body, merged)
            node = DoE(body, None, line=x.line)
            mine = {e for e in x.enums if (e, id(x)) not in used}
            if mine:
                UNUSED[id(node)] = (x.line, sorted(mine, key=x.enums.index), list(x.enums))
            return node
        if env:
            if c is Name and x.name in env:
                used.add(env[x.name])
                return Field(Name(env[x.name][0], line=x.line), x.name, line=x.line)
            if c is PCon and len(x.path) == 1 and x.path[0] in env:
                used.add(env[x.path[0]])
                x.path = [env[x.path[0]][0], x.path[0]]
        for f in x._fields:
            setattr(x, f, rw(getattr(x, f), env))
        return x

    stmts[:] = [rw(s, None) for s in stmts]
    return stmts


def _has_with(x):
    if isinstance(x, (list, tuple)):
        return any(_has_with(i) for i in x)
    if not isinstance(x, N):
        return False
    if x.__class__ is WithE:
        return True
    return any(_has_with(getattr(x, f, None)) for f in x._fields)
