"""moxie command line:  python -m moxie run|test|check FILE [args...]"""
import os
import sys

USAGE = """usage: moxie [--gc] [--release] [--pools] run FILE [args...]     run a program (--gc: moxie/gc rules; --release: contracts off)
       moxie [--allow-read[=PATHS]] [--allow-write[=PATHS]] [--allow-connect[=HOST:PORT]] [--allow-listen[=PORTS]]
             [--allow-ffi[=LIBS]] [--allow-run[=PROGRAMS]] [--allow-stdin] [--allow-env] [--allow-all] [--deny-all] run FILE
                                    restrict what the program may touch (default: a [permissions] table in Moxie.toml, else everything)
       moxie test [--seed N] [--cases N] FILE [name]
                                    run the test blocks (the entry body does not run); forall runs N cases (default 100)
       moxie check FILE             parse and check without running
       moxie pools FILE [--header OUT]  the static pool tally: how many of each counted resource the program creates
       moxie --header=FILE run FILE     start with a pool header: refuse a stale one, hold the program to its counts
       moxie bindgen HEADER (-o FILE | --package NAME) [--lib LIB] [--check]
                                    write foreign declarations from a C header
       moxie doc FILE [-o DIR] [--format md|html] [--private] [--check]
                                    generate documentation from /// comments; checks examples
       moxie fmt [--check] [--stdout] FILE-or-DIR...
                                    rewrite files with canonical layout (2-space indentation, blank lines, no trailing spaces)
       moxie --platform=browser check|run FILE
                                    check or run as Try moxie would: no network or ffi, and calls the browser lacks (signals) are errors
       moxie -e 'code'              run a snippet
"""


PLATFORM = [None]


def make_interp(path, args, perms=None, ceilings=None):
    from .interp import Interp
    from .values import ArrayV, DictV
    I = Interp(search_dir=os.path.dirname(os.path.abspath(path)) if path else ".")
    I.prelude.vars["args"] = ArrayV(list(args))
    if PLATFORM[0] is not None:
        from .perms import Perms
        I.platform = PLATFORM[0]
        I.perms = Perms.browser()
    elif perms is not None:
        I.perms = perms
    if ceilings:
        I.pkg_ceilings = ceilings
    env = {k: v for k, v in os.environ.items()} if I.perms.env_ok() else {}
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
    fa_seed = fa_cases = None
    for opt in ("--seed", "--cases"):
        if opt in argv:
            i = argv.index(opt)
            try:
                val = int(argv[i + 1])
            except (IndexError, ValueError):
                sys.stderr.write(f"moxie: {opt} needs a whole number\n")
                return 2
            del argv[i:i + 2]
            if opt == "--seed":
                fa_seed = val
            else:
                fa_cases = val
    platform = None
    for a in list(argv):
        if a.startswith("--platform="):
            platform = a.split("=", 1)[1]
            argv.remove(a)
    PLATFORM[0] = platform
    if platform is not None:
        from .perms import PLATFORMS
        if platform not in PLATFORMS:
            sys.stderr.write(f"moxie: unknown platform '{platform}' (known: {', '.join(sorted(PLATFORMS))})\n")
            return 2
    want_pools = "--pools" in argv
    argv = [a for a in argv if a != "--pools"]
    # permission flags come before the file name; after it they belong to the program
    pflags, rest, seen_file, header_flag = [], [], False, None
    for a in argv:
        if not seen_file and a.startswith("--header="):
            header_flag = a[len("--header="):]
            continue
        if not seen_file and (a.split("=")[0] in ("--allow-read", "--allow-write", "--allow-connect", "--allow-listen",
                                                  "--allow-ffi", "--allow-run", "--allow-stdin", "--allow-env", "--allow-all", "--deny-all")):
            pflags.append(a)
            continue
        if not seen_file and not a.startswith("-") and a not in ("run", "test", "check", "bindgen", "doc"):
            seen_file = True
        rest.append(a)
    argv = rest
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
    if cmd == "fmt":
        from .fmt import fmt_main
        return fmt_main(argv[1:], sys.stdout, sys.stderr)
    if cmd == "pools":
        if len(argv) < 2:
            sys.stderr.write(USAGE)
            return 2
        from .lexer import MoxieSyntaxError
        try:
            src = open(argv[1], encoding="utf-8").read()
        except OSError as e:
            sys.stderr.write(f"moxie: cannot read {argv[1]}: {e.strerror}\n")
            return 2
        I = make_interp(argv[1], [])
        try:
            prog = I.load_source(src, os.path.basename(argv[1]))
        except MoxieSyntaxError as e:
            sys.stderr.write(str(e) + "\n")
            return 2
        from .tally import Tally, format_tally, format_fibers, format_header
        from .manifest import load as load_manifest, ManifestError
        try:
            man = load_manifest(argv[1])
        except ManifestError as e:
            sys.stderr.write(f"moxie: {e}\n")
            return 2
        t = Tally(prog, man.get("fibers", {}).get("limit"), I.search_dir)
        cnt = t.program()
        sys.stdout.write(format_tally(cnt))
        sys.stdout.write(format_fibers(t))
        for w in t.warnings:
            sys.stdout.write(f"{os.path.basename(argv[1])}: warning: {w}\n")
        for line, msg in t.problems:
            sys.stdout.write(f"{os.path.basename(argv[1])}:{line}: error: {msg}\n")
        if "--header" in argv:
            i = argv.index("--header")
            with open(argv[i + 1], "w") as hf:
                hf.write(format_header(t, cnt, src))
        return 1 if t.problems else 0
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
    from .perms import load_for, load_ceilings, PermError
    from .manifest import load as load_manifest, ManifestError
    try:
        perms = load_for(path, pflags)
        ceilings = load_ceilings(path)
        manifest = load_manifest(path)
    except (PermError, ManifestError) as e:
        sys.stderr.write(f"moxie: {e}\n")
        return 2
    if cmd == "run":
        I = make_interp(path, [a for a in argv[2:] if a != "--no-check"], perms, ceilings)
        I.manifest = manifest
        from .header import prepare, HeaderError
        try:
            prepare(I, src, os.path.basename(path), manifest, header_flag)
        except HeaderError as e:
            sys.stderr.write(f"moxie: {e}\n")
            return 2
        code = I.run_source(src, os.path.basename(path), check="--no-check" not in sys.argv)
        if want_pools:
            sys.stderr.write(I.pools.report())
            if getattr(I, "main_prog", None) is not None:
                from .tally import static_tally, format_tally, compare
                cnt = static_tally(I.main_prog, I.manifest.get("fibers", {}).get("limit"), I.search_dir)
                sys.stderr.write(format_tally(cnt))
                for w in compare(cnt, I.pools):
                    sys.stderr.write(w + "\n")
        return code
    if cmd == "test":
        I = make_interp(path, [], perms, ceilings)
        I.manifest = manifest
        I.forall_seed, I.forall_cases = fa_seed, fa_cases
        p_, f_, code = I.run_tests(src, os.path.basename(path), argv[2] if len(argv) > 2 else None)
        if "/// >" in src and len(argv) <= 2:
            from .doc import collect, run_doctests
            clean, _, items = collect(src)
            for it, e, x, ok, msg in run_doctests(src, items, lambda: make_interp(path, [])):
                print(("ok    " if ok else "FAIL  ") + f"doctest {it.name}: {e}" + ("" if ok else f" ({msg})"))
                code = code or (0 if ok else 1)
        return code
    if cmd == "check":
        I = make_interp(path, [], perms, ceilings)
        I.manifest = manifest
        return I.check_source(src, os.path.basename(path))
    return 2


if __name__ == "__main__":
    try:
        code = main()
        sys.stdout.flush()
    except BrokenPipeError:
        code = 0
    sys.exit(code)
