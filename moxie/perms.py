"""Permissions (Spec section 19d): what a program may touch outside its own memory.

Kinds: fs.read and fs.write (path prefixes), net.connect ("host:port" patterns), net.listen (ports),
ffi (library names), stdin, env.  stdout and stderr are always allowed.  A program run with no
permission settings is unrestricted; a Moxie.toml with a [permissions] table, or any --allow-* /
--deny-all flag, restricts it to what is granted.  A denied call gives Err(DENIED); loading a
foreign library that is not granted stops the program before it runs.
"""
import fnmatch
import os

# Platforms (Spec 19e): calls that can never work there, found at check time like a missing permission.
PLATFORMS = {"browser": {"label": "the browser", "missing": ("platform:signals",)}}

KINDS = ("fs.read", "fs.write", "net.connect", "net.listen", "ffi", "stdin", "env")


class PermError(Exception):
    pass


class Perms:
    def __init__(self, restricted=False, base="."):
        self.restricted = restricted
        self.base = os.path.abspath(base)
        self.grants = {k: [] for k in KINDS}       # kind -> list of patterns; "*" = everything
        self.source = "unrestricted"

    # ---------------------------------------------------------------- building
    @classmethod
    def open(cls):
        return cls(False)

    @classmethod
    def none(cls, base="."):
        return cls(True, base)

    @classmethod
    def browser(cls):
        """What Try moxie grants: files (an in-memory file system), stdin text, and env, but no network and no ffi."""
        pm = cls(True, ".")
        pm.source = "the browser"
        for k in ("fs.read", "fs.write", "stdin", "env"):
            pm.grant(k)
        return pm

    def grant(self, kind, pats=None):
        if kind not in self.grants:
            raise PermError(f"unknown permission '{kind}'")
        if pats is None or pats is True:
            pats = ["*"]
        for p in ([pats] if isinstance(pats, (str, int)) else pats):
            self.grants[kind].append(str(p))

    @classmethod
    def from_manifest(cls, table, base, where="Moxie.toml"):
        """`table` is the parsed [permissions] table."""
        pm = cls(True, base)
        pm.source = where
        known = {"fs", "net", "ffi", "stdin", "env", "all", "packages"}
        for k in table:
            if k not in known:
                raise PermError(f"{where}: unknown permission '{k}' in [permissions] (known: {', '.join(sorted(known))})")
        if "all" in table:
            if not isinstance(table["all"], bool):
                raise PermError(f"{where}: 'all' must be true or false")
            if table["all"]:
                for kind in KINDS:
                    pm.grant(kind)
        for k, subs in (("fs", ("read", "write")), ("net", ("connect", "listen"))):
            v = table.get(k)
            if v is None:
                continue
            if v is True:
                for s in subs:
                    pm.grant(f"{k}.{s}")
            elif isinstance(v, dict):
                for s, pats in v.items():
                    if s not in subs:
                        raise PermError(f"{where}: unknown permission '{k}.{s}' (known: {', '.join(k + '.' + x for x in subs)})")
                    pm._grant_checked(f"{k}.{s}", pats, where)
            elif v is not False:
                raise PermError(f"{where}: '{k}' must be true or a table with {' and '.join(subs)}")
        for k in ("ffi",):
            if k in table:
                pm._grant_checked(k, table[k], where)
        for k in ("stdin", "env"):
            if k in table:
                if not isinstance(table[k], bool):
                    raise PermError(f"{where}: '{k}' must be true or false")
                if table[k]:
                    pm.grant(k)
        return pm

    def _grant_checked(self, kind, pats, where):
        if pats is True:
            self.grant(kind)
        elif pats is False:
            pass
        elif isinstance(pats, list) and all(isinstance(x, (str, int)) and not isinstance(x, bool) for x in pats):
            self.grant(kind, pats)
        else:
            raise PermError(f"{where}: '{kind}' must be true or a list of strings")

    # ---------------------------------------------------------------- queries
    def allows_kind(self, kind):
        """Static question: is anything of this kind granted at all?"""
        return (not self.restricted) or bool(self.grants[kind])

    def _has(self, kind):
        return (not self.restricted) or "*" in self.grants[kind]

    def path_ok(self, kind, path):
        if not self.restricted or "*" in self.grants[kind]:
            return True
        p = os.path.realpath(os.path.join(self.base, str(path)))
        for g in self.grants[kind]:
            root = os.path.realpath(os.path.join(self.base, g))
            if p == root or p.startswith(root.rstrip(os.sep) + os.sep):
                return True
        return False

    def connect_ok(self, host, port):
        if not self.restricted:
            return True
        for g in self.grants["net.connect"]:
            if g == "*":
                return True
            h, _, pt = g.rpartition(":")
            if (fnmatch.fnmatchcase(str(host), h or "*")) and (pt == "*" or pt == str(port)):
                return True
        return False

    def listen_ok(self, port):
        if not self.restricted:
            return True
        for g in self.grants["net.listen"]:
            if g == "*" or g == str(port):
                return True
            if "-" in g:
                lo, _, hi = g.partition("-")
                if lo.isdigit() and hi.isdigit() and int(lo) <= int(port) <= int(hi):
                    return True
        return False

    def ffi_ok(self, lib):
        return (not self.restricted) or "*" in self.grants["ffi"] or str(lib) in self.grants["ffi"]

    def stdin_ok(self):
        return self._has("stdin")

    def env_ok(self):
        return self._has("env")

    def describe(self):
        if not self.restricted:
            return "unrestricted"
        parts = []
        for k in KINDS:
            g = self.grants[k]
            if g:
                parts.append(f"{k}=" + ("all" if "*" in g else ",".join(g)))
        return "; ".join(parts) or "nothing granted"


FLAG_KINDS = {"--allow-read": "fs.read", "--allow-write": "fs.write", "--allow-connect": "net.connect",
              "--allow-listen": "net.listen", "--allow-ffi": "ffi", "--allow-stdin": "stdin", "--allow-env": "env"}


def from_flags(flags, base):
    """flags: the --allow-*/--deny-all/--allow-all arguments.  Returns Perms or None when there are none."""
    if not flags:
        return None
    pm = Perms.none(base)
    pm.source = "command line"
    for fl in flags:
        name, eq, val = fl.partition("=")
        if name == "--allow-all":
            pm = Perms.open()
            pm.source = "command line"
        elif name == "--deny-all":
            pass
        elif name in FLAG_KINDS:
            if not pm.restricted:
                continue
            kind = FLAG_KINDS[name]
            pm.grant(kind, [x for x in val.split(",") if x] if eq else None)
        else:
            raise PermError(f"unknown option '{name}'")
    return pm


def find_manifest(path):
    d = os.path.dirname(os.path.abspath(path))
    while True:
        m = os.path.join(d, "Moxie.toml")
        if os.path.isfile(m):
            return m
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up


def load_for(path, flags):
    """The permissions for running `path`: flags win, else a [permissions] table in the nearest Moxie.toml, else unrestricted."""
    base = os.path.dirname(os.path.abspath(path)) if path else "."
    pm = from_flags(flags, os.getcwd())
    if pm is not None:
        return pm
    if path:
        m = find_manifest(path)
        if m:
            import tomllib
            try:
                with open(m, "rb") as f:
                    data = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                raise PermError(f"{m}: {e}")
            if "permissions" in data:
                if not isinstance(data["permissions"], dict):
                    raise PermError(f"{m}: [permissions] must be a table")
                return Perms.from_manifest(data["permissions"], os.path.dirname(m), m)
    return Perms.open()


class Combined:
    """What code in a package may do: the program's grants and the package's own ceiling must both allow it."""
    restricted = True

    def __init__(self, program, ceiling, pkg):
        self.program, self.ceiling, self.pkg = program, ceiling, pkg
        self.source = ceiling.source

    def _both(self, ok_a, ok_b):
        if not (ok_a and ok_b):
            CURRENT[0] = self.pkg
            return False
        return True

    def allows_kind(self, kind):
        return self._both(self.program.allows_kind(kind), self.ceiling.allows_kind(kind))

    def path_ok(self, kind, path):
        return self._both(self.program.path_ok(kind, path), self.ceiling.path_ok(kind, path))

    def connect_ok(self, host, port):
        return self._both(self.program.connect_ok(host, port), self.ceiling.connect_ok(host, port))

    def listen_ok(self, port):
        return self._both(self.program.listen_ok(port), self.ceiling.listen_ok(port))

    def ffi_ok(self, lib):
        return self._both(self.program.ffi_ok(lib), self.ceiling.ffi_ok(lib))

    def stdin_ok(self):
        return self._both(self.program.stdin_ok(), self.ceiling.stdin_ok())

    def env_ok(self):
        return self._both(self.program.env_ok(), self.ceiling.env_ok())

    def describe(self):
        return f"package {self.pkg}: {self.ceiling.describe()}, within the program's {self.program.describe()}"


CURRENT = [None]          # the package named in the last refusal, for the message of `denied`


def load_ceilings(path):
    """{package name: Perms} from [permissions.packages.NAME] tables in the nearest Moxie.toml."""
    if not path:
        return {}
    m = find_manifest(path)
    if not m:
        return {}
    import tomllib
    try:
        with open(m, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise PermError(f"{m}: {e}")
    perm = data.get("permissions")
    if not isinstance(perm, dict) or "packages" not in perm:
        return {}
    pk = perm["packages"]
    if not isinstance(pk, dict):
        raise PermError(f"{m}: [permissions.packages] must hold one table per package")
    out = {}
    for name, table in pk.items():
        if not isinstance(table, dict):
            raise PermError(f"{m}: [permissions.packages.{name}] must be a table")
        if "packages" in table or "all" in table:
            raise PermError(f"{m}: [permissions.packages.{name}] cannot contain 'all' or 'packages'")
        out[name] = Perms.from_manifest(table, os.path.dirname(m), f"{m} [permissions.packages.{name}]")
    return out
