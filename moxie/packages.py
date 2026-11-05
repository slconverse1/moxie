"""Finding a package's files (Spec section 4).

`import a.b` looks, from the importing program's folder, for
  1. a/b.mxi                         one file
  2. a/b/Moxie.toml with `files`     several files, compiled in that order
  3. a/b/b.mxi                       one file in a folder
and then in the packages that ship with the interpreter (stdpkg.py).  A program's own files win.
"""
import os


class PackageError(Exception):
    pass


def package_files(search_dir, parts):
    """([paths in compile order], folder or None) for the package, or None when there is none."""
    base = search_dir or "."
    d = os.path.join(base, *parts)
    one = d + ".mxi"
    if os.path.isfile(one):
        return [one], None
    man = os.path.join(d, "Moxie.toml")
    if os.path.isfile(man):
        import tomllib
        try:
            with open(man, "rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError) as e:
            raise PackageError(f"{man}: {e}")
        files = data.get("files")
        if files is not None:
            if not isinstance(files, list) or not files or not all(isinstance(x, str) for x in files):
                raise PackageError(f"{man}: files must be a list of file names")
            paths = [os.path.join(d, x) for x in files]
            for p in paths:
                if not os.path.isfile(p):
                    raise PackageError(f"{man}: the file {os.path.basename(p)!r} is listed in files but does not exist")
            return paths, d
    folder_one = os.path.join(d, parts[-1] + ".mxi")
    if os.path.isfile(folder_one):
        return [folder_one], d
    from .stdpkg import find_std
    s = find_std(parts)
    return ([s], None) if s else None


def parse_package(paths):
    """(source text, one program) for a package's files, joined in order."""
    from .parser import parse_program
    from .ast import Block
    srcs, stmts = [], []
    for p in paths:
        src = open(p, encoding="utf-8").read()
        srcs.append(src)
        stmts.extend(parse_program(src, p).stmts)
    return "\n".join(srcs), Block(stmts, line=1)
