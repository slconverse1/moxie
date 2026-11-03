"""moxie command line:  python -m moxie run|test|check FILE [args...]"""
import os
import sys

USAGE = """usage: moxie [--gc] [--release] run FILE [args...]     run a program (--gc: moxie/gc rules; --release: contracts off)
       moxie test FILE [name]       run the test blocks (the entry body does not run)
       moxie check FILE             parse and check without running
       moxie bindgen HEADER (-o FILE | --package NAME) [--lib LIB] [--check]
                                    write foreign declarations from a C header
       moxie doc FILE [-o DIR] [--format md|html] [--private] [--check]
                                    generate documentation from /// comments; checks examples
       moxie -e 'code'              run a snippet
"""


def make_interp(path, args):
    from .interp import Interp
    from .values import ArrayV, DictV
    I = Interp(search_dir=os.path.dirname(os.path.abspath(path)) if path else ".")
    I.prelude.vars["args"] = ArrayV(list(args))
    env = {k: v for k, v in os.environ.items()}
    I.prelude.vars["env"] = DictV(env, len(env))
    return I


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--gc" in argv:
        from .values import GC
        GC[0] = True
        argv = [a for a in argv if a != "--gc"]
    if "--release" in argv:
        from .values import CONTRACTS
        CONTRACTS[0] = False
        argv = [a for a in argv if a != "--release"]
    sys.setrecursionlimit(100000)
    if not argv or argv[0] in ("-h", "--help", "help"):
        sys.stdout.write(USAGE)
        return 0 if argv else 2
    if argv[0] == "-e":
        I = make_interp(None, [])
        return I.run_source(argv[1], "<-e>")
    cmd = argv[0]
    if cmd == "bindgen":
        from .bindgen import main as bg_main
        return bg_main(argv[1:])
    if cmd == "doc":
        from .doc import doc_main
        return doc_main(argv[1:], lambda: make_interp(argv[1] if len(argv) > 1 else None, []),
                        sys.stdout, sys.stderr)
    if cmd not in ("run", "test", "check"):
        cmd, argv = "run", ["run"] + argv
    if len(argv) < 2:
        sys.stderr.write(USAGE)
        return 2
    path = argv[1]
    try:
        src = open(path, encoding="utf-8").read()
    except OSError as e:
        sys.stderr.write(f"moxie: cannot read {path}: {e.strerror}\n")
        return 2
    if cmd == "run":
        I = make_interp(path, [a for a in argv[2:] if a != "--no-check"])
        return I.run_source(src, os.path.basename(path), check="--no-check" not in sys.argv)
    if cmd == "test":
        I = make_interp(path, [])
        p_, f_, code = I.run_tests(src, os.path.basename(path), argv[2] if len(argv) > 2 else None)
        if "/// >" in src and len(argv) <= 2:
            from .doc import collect, run_doctests
            clean, _, items = collect(src)
            for it, e, x, ok, msg in run_doctests(src, items, lambda: make_interp(path, [])):
                print(("ok    " if ok else "FAIL  ") + f"doctest {it.name}: {e}" + ("" if ok else f" ({msg})"))
                code = code or (0 if ok else 1)
        return code
    if cmd == "check":
        I = make_interp(path, [])
        return I.check_source(src, os.path.basename(path))
    return 2


if __name__ == "__main__":
    try:
        code = main()
        sys.stdout.flush()
    except BrokenPipeError:
        code = 0
    sys.exit(code)
