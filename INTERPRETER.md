# Moxie interpreter (v1)

A pure-Python interpreter for the frozen Moxie language. No C extensions, no threads, standard library only
(`sqlite3` for SQL), so it also runs in the browser under Pyodide.

    python -m moxie run FILE [args...]   run a program (core static checks run first; --no-check skips them)
    python -m moxie test FILE [name]     run the `test` blocks, each in its own fiber; the entry body does not run
    python -m moxie check FILE           parse and run the static checks only
    python -m moxie -e 'println("hi")'   run a snippet
    python -m moxie --gc run FILE        run under the moxie/gc rules (or set MOXIE_GC=1)

Exit codes: 0 ok, 1 runtime abort or failed test, 2 syntax or compile error.

## What it does
* Runs everything in the Spec and Guide that is not marked "not designed": declarations, enums, patterns, generics,
  interfaces and impls, `F[_]` constructor classes, pipes, `for:` comprehensions, streams, data paths, fixed-capacity
  collections, sized/bounded/Big/Decimal numbers, format specs and `Locale`.
* Fibers, channels, timers, futures, atoms, `select:`, `daemon:` and `run` on a generator-based cooperative scheduler
  with a virtual clock (`sleep` and timers advance instantly and deterministically).
* `sql(conn):` and `transaction(conn)(tx):` on sqlite3. `Connection.open(path)` and `Connection.memory()` create connections.
* Core static checks (see `moxie/check.py`): mismatched types, undefined names, argument counts, `ref` mismatches,
  non-exhaustive `when` (enums, Result, Bool, bounded ranges, literals without `_`), use-after-move and moves inside
  loops, resource copies, and bounded-integer misuse. It also checks interface bounds at call sites (`best[T: Ordered]`
  called with a type that has no `Ordered` impl is an error), `deriving` clauses (`hash` needs `eq`; `Hashable` can only
  be derived), and relational patterns (`>= 500 ->`). The checker is conservative: whatever it cannot type is
  unknown and never an error.
* The prelude interfaces `Equatable`, `Ordered`, `Hashable`, `Show`, `Read`, `Addable` and `Numeric`, including
  `T.zero()`, `T.one()` and `T.read(text)` inside generic code.
* Argument-first `run` (`run fn (tx, start)(out, first): ...`) and params-first plain calls (`fn (x: Int)(21)`).

## Since the first release
The prelude has `distinct`, `intersperse`, `flatten`, `cycle`, `zip_with`, `reduce_right`, `min_by`, `max_by`, `span`, and `split_at`. A function clause may carry an `if` guard, and `tailrec fn` makes a self-call outside tail position a compile error. `moxie fmt`, doctests, and property tests are designed in the Spec (section 22) but not built.

## moxie/gc mode
`--gc` (or `MOXIE_GC=1`) runs a program under the moxie/gc rules that an interpreter can show: `List`, `Set`, and `Dict`
have no fixed capacity (a size in brackets is only a hint, and `Array` keeps its size), `put` returns the updated
collection, a variadic parameter is a `List`, a channel capacity may be any `Int` expression, and `Chan[T][#unbounded]()`
is accepted. `copy` is an error. The prelude additions `Ring[T](n)` and `take_last(n)` are available. Closures, streams, and recursive values already behave as moxie/gc describes, because
this interpreter never enforced the memory-space rules. It has no collector, no heap limit, and no allocation report, so
those parts of moxie/gc are not modeled.

## Tests
    python tests/run_guide.py     every Guide example against its hand-computed output (174 blocks)
    python tests/run_checks.py    negative cases for the static checks (36 cases)
    python tests/run_helpers.py   stream helpers, clause guards, and `tailrec`, in both dialects (26 checks)
    python tests/run_gc.py        programs that rely on the moxie/gc rules (16 cases)
    python tests/run_gc_guide.py  every moxie/gc Guide example under --gc

## Examples
`examples/gradebook.mxi` is the program built step by step in the Moxie Tutorial. Run it with
`python -m moxie run examples/gradebook.mxi`, or its test with `python -m moxie test examples/gradebook.mxi`.
`examples/gradebook_gc.mxi` is the same program for moxie/gc, with the memory step added; run it with `python -m moxie --gc run examples/gradebook_gc.mxi`.

## Not in v1
Full type inference. Generic bounds are checked only for parameters typed directly as the type parameter, and
size parameters, `where N > 0` and Dict key eligibility are not checked. Pool/stack sizing and memory spaces (S-space/T-space),
the SQL schema check, `moxie build`/`--release`, package manifests and lockfiles, and everything the Spec marks "not designed".
Memory limits are not enforced: collection capacity is.

See FIXLIST.md for the problems found in the Spec and Guide.

## moxie doc (first prototype)

    moxie doc FILE [-o DIR] [--format md|html] [--private] [--check]

Builds documentation from `///` comments (`//!` for module docs). It shows each
exported item's signature (all items if none are exported, or with `--private`),
doc text, contract lines (`requires` / `ensures` / `invariant`), implementors of
interfaces, and the `> expr` / expected-output examples, which are run as
doctests. `--check` exits nonzero on a failing example or a broken
``[`name`]`` link and warns about undocumented exports. `moxie test FILE` also
runs the doctests. Not yet built: effect display, the full Markdown subset,
cross-module pages. Contracts are enforced by the interpreter (see below). See `examples/documented.mxi` and `tests/run_doc.py`.

## Contracts (first prototype)

`requires` and `ensures` lines may start a function body; `invariant` lines may
appear among a tuple's fields. `ensures` sees the return value as `result`.
A failing `requires` aborts with "caller bug"; a failing `ensures` or
`invariant` aborts with "supplier bug". Invariants are checked when a tuple is
constructed. Contracts on interface members are checked whenever an
implementation of that member runs (the interface's parameter names are mapped
onto the implementation's). `moxie --release run FILE` turns all checks off. Not
yet built: a compile error for constant arguments that fail `requires`,
or the manifest key that keeps contracts in release builds. An `impl` of an
interface that adds its own contracts is a compile error. See
`tests/run_contracts.py`.

## Effect inference (first version)

`moxie check` (and `run`, which checks first) infers whether each function
parks (`read`, `write`, `sleep`, a `select` with no default arm, a database
query) or prints, through callees and recursion. A call through a function
parameter takes the effect of the function passed at the call site. Methods are
resolved by name (the union over every function or method with that name).
It reports: a `pure fn` that has an effect, a function given to `swap` that may
park, a `debug_assert` condition that has an effect, and a contract condition
that has an effect. `moxie doc` shows each function's effects. Effect
declarations (`pure`, `prints`, `parks`, `impure` before `fn`) are checked in
both directions; on a bodyless interface member or forward declaration they are
an upper bound for the impls. Not yet built: the "resource" effect, and reading `read(x)` as text versus a channel by type (a call
`read(x)` is taken to park; `read[T](x)` does not). See `tests/run_effects.py`.

## NonEmpty

`non_empty(list)` returns `Ok(NonEmpty)` or `Err(Error(MISSING, "empty"))`.
`NonEmpty` is written in moxie itself (`moxie/mxprelude.py`) and has `to_list`,
`len`, `to_stream`, `map`, `reduce1`, `min`, and `max`. The reserved error codes
(`MISSING`, `CLOSED`, ...) are now bound as names.

`trace(msg)` writes `[trace FILE:LINE] msg` to the error stream, is exempt from
effect inference, and does nothing under `--release` (as does `debug_assert`).

`curry(f)` works for a function of two or more parameters, read from its
declaration at run time (`curry2` to `curry6` remain). `uncurry[n](g)` is the
inverse, with `n` a constant in brackets (2 or more, no upper limit); calling the
result with another number of arguments aborts. The checker has no special
typing rule for either yet.

## Foreign functions and `moxie bindgen` (first version)

`foreign "lib":` blocks of body-less declarations call C libraries through
`ctypes` (`moxie/ffi.py`). Every declaration needs an effect (`pure`, `prints`,
`parks`, `impure`); a missing one is a compile error, and the declared effects
are what the checker uses for callers. Supported across the boundary: fixed-width
integers, `Int`/`UInt`, `Float`, `Double`, `Bool`, tuples of those (C structs, by
value), `Array[Byte]` (a pointer, with `n: T = len(name)` as the length that the
call fills in, and `ref` for a writable buffer), `CString` (made by `cstr(text)`),
and `ref` out-parameters of scalars and tuples. A library is found by its name,
in the program's directory (`libNAME.so`), or in `MOXIE_NATIVE_PATH`. Not yet
built: handles through out-parameters, a pool tally for handles, callbacks, running
`parks` functions on a helper thread (they run inline), and reading `[native]`
from a manifest. Tests: `tests/run_ffi.py`.

Handles: `handle Name closes fn` in a `foreign` block makes `Name` an opaque
pointer type (`HandleV` in `ffi.py`). The checker treats a function that returns
`Name` or `Result[Name, Error]` as a resource maker, so `move` and use-after-move
rules apply, and a call to the closing function consumes its argument. At run
time a closed handle used again aborts, a NULL result is `Err(MISSING)` (or an
abort for a plain `Name`), and handles still open at program end are closed.
`moxie bindgen` emits handle declarations and finds the closer by name or from
`[handles.NAME] closes` in `bindgen.toml`. Tests: `tests/run_handles.py`.

    moxie bindgen HEADER (-o FILE | --package NAME) [--lib LIB] [--check] [-D X] [-I DIR]

writes the declarations from a C header (needs `gcc` and `pip install pycparser`).
Corrections go in `bindgen.toml` next to the output: `[functions.NAME]` with
`effects`, `skip`, or `pair = ["buf", "len"]`. Functions it cannot declare are
left as `// todo:` comments and listed in its report. Tests: `tests/run_bindgen.py`.

## Standard input and output

`stdin`, `stdout`, `stderr` are `StdStream` values in `prelude.py` (borrowed:
never moved or closed). `print`/`println` take an optional stream first;
`eprint`/`eprintln`, `flush`, `read_line()`, `read_all()`, `stdin_lines()` and
`with_stdin(text, f)` are builtins. The reads are `parks` in `effects.py`. The
interpreter reads `Interp.inp` (default `sys.stdin`; tests pass their own).
Input is UTF-8; bad bytes give `Err` code `BAD_ENCODING`. Tests:
`tests/run_stdio.py`.
