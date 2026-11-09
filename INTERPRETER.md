# Moxie interpreter (v1)

A pure-Python interpreter for the frozen Moxie language. No C extensions, no threads, standard library only
(`sqlite3` for SQL), so it also runs in the browser under Pyodide.

    python -m moxie run FILE [args...]   run a program (core static checks run first; --no-check skips them)
    python -m moxie test [--seed N] [--cases N] FILE [name]
                                         run the `test` blocks, each in its own fiber; the entry body does not run
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
* The `[database]` manifest table (`schema`, `driver`) names a `CREATE TABLE` schema file; `sql` blocks are checked against it: the accepted SQL subset, and that every table and column exists. Column types and row types are not worked out yet. Tests: `tests/run_sqlcheck.py`.
* Core static checks (see `moxie/check.py`): mismatched types, undefined names, argument counts, `ref` mismatches,
  non-exhaustive `when` (enums, Result, Bool, bounded ranges, literals without `_`), use-after-move and moves inside
  loops, resource copies, and bounded-integer misuse. It also checks interface bounds at call sites (`best[T: Ordered]`
  called with a type that has no `Ordered` impl is an error), `deriving` clauses (`hash` needs `eq`; `Hashable` can only
  be derived), and relational patterns (`>= 500 ->`). The checker is conservative: whatever it cannot type is
  unknown and never an error.
* The prelude interfaces `Equatable`, `Ordered`, `Hashable`, `Show`, `Read`, `Addable` and `Numeric`, including
  `T.zero()`, `T.one()` and `T.read(text)` inside generic code.
* Argument-first `run` (`run fn (tx, start)(out, first): ...`). The parameters-first immediately-called form is gone; wrap the lambda, `((x: Int): x * 2)(21)`.
* Lambdas have no `fn`: `(params): body` is recognized in `pexpr.parse_atom` by looking past the matching `)` for a colon (or a return type and a colon), except at the top level of a header, where the colon belongs to the header. `fn (params): body` is an anonymous function that may have effects (the parser sets `fiber` on it, as for an inline `run fn`). A typed binding may carry a function type, `add: (Int, Int) -> Int = (a, b): a + b`. `Lambda` has two flags the parser sets, `partial` (a call with `_`) and `fiber` (effects allowed: an inline `run fn` or an anonymous `fn`). `effects.check_lambdas` reports an effect in a lambda, a bound lambda that mentions its own name, and `run` of a name bound to a lambda. A builder callback takes its receiver from the expected function type.

## Since the first release
The prelude has `distinct`, `intersperse`, `flatten`, `cycle`, `zip_with`, `reduce_right`, `min_by`, `max_by`, `span`, and `split_at`. A function clause may carry an `if` guard, and `tailrec fn` makes a self-call outside tail position a compile error. Doctests and property tests are designed in the Spec (section 22) but not built.

## moxie/gc mode
`--gc` (or `MOXIE_GC=1`) runs a program under the moxie/gc rules that an interpreter can show: `List`, `Set`, and `Dict`
have no fixed capacity (a size in brackets is only a hint, and `Array` keeps its size), `put` returns the updated
collection, a variadic parameter is a `List`, a channel capacity may be any `Int` expression, and `Chan[T][#unbounded]()`
is accepted. `copy` is an error. The prelude additions `Ring[T](n)` and `take_last(n)` are available. Closures, streams, and recursive values already behave as moxie/gc describes, because
this interpreter never enforced the memory-space rules. It has no collector and no allocation report. `[memory] heap` is enforced by `moxie/heap.py` (below);
`slice` and the generations are not modeled.

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
`where N > 0` and Dict key eligibility are not checked (Spec section 24a lists every gap). Pool/stack sizing and memory spaces (S-space/T-space),
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
declaration at run time. `uncurry[n](g)` is the
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
built: handles through out-parameters, a pool tally for handles, callbacks, static linking, and the lockfile. `[native]` (`libs`, `paths`) is read for the entry package and for an imported package folder (`manifest.native_table`, `package_native`); `Interp.native_diags` reports a package whose manifest has no `[native]`, or a library not in `libs`, at check time (`moxie check` and before a run; `decls.ev_ForeignDecl` repeats the test as a backstop), and `paths` go first in `ffi.load_library`. Tests: `tests/run_ffi.py` and `tests/run_native.py`.

Handles: `handle Name closes fn` in a `foreign` block makes `Name` an opaque
pointer type (`HandleV` in `ffi.py`). The checker treats a function that returns
`Name` or `Result[Name, Error]` as a resource maker, so `move` and use-after-move
rules apply, and a call to the closing function consumes its argument. At run
time a closed handle used again aborts, a NULL result is `Err(MISSING)` (or an
abort for a plain `Name`), and handles still open at program end are closed.
`moxie bindgen` emits handle declarations and finds the closer by name or from
`[handles.NAME] closes` in `bindgen.toml`. Tests: `tests/run_handles.py`.

    moxie bindgen HEADER (-o FILE | --package NAME) [--lib LIB] [--check] [--wrap] [-D X] [-I DIR]

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

## Files and sockets

`IoV` and `ListenerV` in `prelude.py` wrap binary Python file objects and
sockets. `open_file(path, mode)` takes the prelude enum `FileMode`
(`ReadOnly`, `Create`, `Append`, `ReadWrite`, defined in `mxprelude.py`).
`read_line`, `read_all`, `lines`, `print`, `println`, `flush` accept an `Io`;
`read_bytes`, `write_bytes`, `read_file`, `write_file`, `connect`, `listen`,
`port_of`, `accept` are builtins, all `parks` in `effects.py`. The checker treats
`open_file`, `connect`, `listen`, `accept` as resource makers and `Io`/`Listener`
as resource types. Errors map to `NOT_FOUND`, `DENIED`, `IO_ERROR`. Anything
still open at program end is closed. Blocking calls use OS helper threads (see below). Tests: `tests/run_io.py`.

## OS helper threads

`sched.park_thread(I, fn)` (use `r = yield from park_thread(I, fn)`) runs `fn()` on a
daemon thread while the calling fiber is blocked; the scheduler keeps running
other fibers, and its loop drains finished calls from a queue. When nothing else is
ready and calls are in flight, it waits for one in real time before advancing
virtual time, and in-flight calls are not a deadlock. Exceptions are carried back
(`ExtFail`) and re-raised in the fiber. Used by `read_line`, `read_all`,
`read_bytes`, `lines`, `connect`, `accept` (in-memory input, as in `with_stdin`,
stays inline) and by foreign functions declared `parks` (`ffi.call_foreign` is now
a generator). The thread function must not touch interpreter state.

## FFI callbacks

A function-typed parameter of a foreign function (`f: (Double) -> Double`) becomes a
`ctypes.CFUNCTYPE` thunk made per call (`ffi.make_thunk`). The thunk converts C
arguments, runs the moxie function to completion with `ffi.run_sync` (a callback
that parks aborts), and converts the result. An exception in a callback is stored,
the thunk returns zero, and the call re-raises it when the foreign function returns.
A foreign function with a callback cannot be `parks` (checked in `check.py` and
`make_foreign`). In `effects.py` the callback argument must not park and its other
effects count against the caller. `moxie bindgen` turns a function pointer with
scalar/tuple parameters and result into a function type, and leaves the rest as
todos. Tests: `tests/run_callbacks.py`.

## Handle out-parameters

A `ref p: H` parameter with `H` a handle type is a `void **` that `call_foreign` fills
in (`ffi.is_out_handle`); the checker drops it (and length parameters) from the
caller's argument list (`check.hidden_foreign_param`). A `Result[H, Error]` result
reads C's `int` status (0 is success; otherwise `Err` with the status as the code,
closing any handle C left); a plain `H` result ignores C's result and aborts on NULL.
`moxie bindgen` turns `T **` to an opaque struct into such a parameter. Tests:
`tests/run_handles.py`, `tests/run_bindgen.py`.

## Observed pool report

The compiler's static pool tally does not exist yet. `moxie --pools run FILE` prints,
to stderr after the run, how many files and sockets (`Io file`, `Io socket`),
listeners, foreign handles (`handle NAME`), connections, channels, futures, timers,
and atoms were open at once and in total (`moxie/pools.py`). A resource that goes out
of scope without being closed is not noticed until its fiber or the program ends, so
peaks can over-count; timers and atoms are never released. Tests: `tests/run_pools.py`.

## Callback buffers and user data

In a callback's function type, `ffi.cb_plan` maps C's arguments to the moxie function's:
an `Array[Byte]` followed by an integer type is C's (pointer, length) pair and becomes
one array (a copy, read from the pointer with `ctypes.string_at`), and `UserData` is a
`void *` that is not passed on. A `ud: UserData` parameter of the foreign function is
hidden from callers (the checker and `effects.py` leave it out of the argument list)
and C is given NULL. `moxie bindgen` recognizes `void *` next to a callback as
`UserData` and a byte pointer followed by an integer in a callback as a buffer.
Tests: `tests/run_callbacks.py`, `tests/run_bindgen.py`.

## `moxie bindgen --wrap`

`bindgen.make_wrappers` writes `wrappers.mxi` next to the bindings. The generator
records, for every declared function, its visible parameters and result
(`Gen.fn_info`); a wrapper converts `CString` to `String` (calling `cstr`), hides
`UserData` and length parameters in callback types (`clean_cb`), keeps the raw effect
declaration, and for an int status with out-parameters (names `out`/`result`/`res`/`ret`,
or `outs = [...]` in `bindgen.toml`) returns `Result[T, Error]` using `fail(status, ...)`.
`returns = "status" | "value"` overrides the guess. Names: library prefix removed, a
trailing underscore when the result would hide a prelude function or repeat a name
(`wrapper_names`). The report lists each status guess. Tests: `tests/run_bindgen.py`.

## `bindgen.toml`

Keys: top-level `lib`; `[functions.NAME]` with `effects`, `skip`, `pair`, `returns`,
`outs`, `rename`; `[handles.TYPE]` with `closes`. `bindgen.validate_sidecar` checks the
shape on every run (errors name the file and key and suggest the nearest valid key;
exit code 2), and `unused_sidecar` warns about entries that match no function or handle
in the header. Tests: `tests/run_bindgen.py`.

## Callbacks that C keeps (`Events[T]`)

A foreign parameter `cb: Events[T]` takes a channel write end (`move tx`; the checker
requires `move`). `ffi.make_event_thunk` builds a C-callable thunk that converts the
arguments (`convert_args`, the same plan as ordinary callbacks) and calls
`Scheduler.post_event`, which puts the message on the thread-safe queue; the scheduler
loop (`drain_ext`) delivers it with `deliver_event`: wake a waiting reader, else buffer
it, else drop it (counted in `EventSink.dropped` and reported at exit). The thunk is
kept in `Interp.kept_thunks` forever and `Scheduler.listeners` is incremented, so an
idle loop waits for events instead of reporting a deadlock. Tests:
`tests/run_callbacks.py` (a C library that calls from its own pthread),
`tests/run_bindgen.py` (`keeps`).

## Arrays of numbers, `Ptr[T]`, and `Handler[F]`

`ffi.array_elem` generalizes the byte-array path: any `Array[T]` of a scalar type is copied
into a ctypes array (`array_to_c`), and a `ref` array is copied back (`array_from_c`). A
parameter written `size: UInt = size_of(a)` (`size_of_param`; hidden from callers like `len`,
in `check.hidden_foreign_param` and `effects`) is filled with `sizeof` of the element.
In callback types `cb_plan` has two more entries: `("array", elem, lenctype)` and `("ptr", T)`
(a `const T *` read once and passed as the value). `qsort` works from libc in
`tests/run_callbacks.py`. bindgen maps a number pointer followed by a length to `Array[T]`
and a callback's const number pointer to `Ptr[T]`.

`Handler[F]` is a kept callback that must answer. `ffi.make_handler_thunk`: on the
scheduler's thread the function runs at once through `run_sync`; on any other thread the
call goes to `Scheduler.post_call`, `deliver_call` spawns a fiber (so the function may park)
and the C thread waits on a `queue.Queue` for `("ok", result)` or `("err", None)` (zeros to C,
then the abort ends the program). `Scheduler.handlers` counts waiting handler fibers: with
one and a sleeper pending, `run_main` advances virtual time instead of blocking on the
thread queue (otherwise a sleeping handler and a thread waiting on it would deadlock).
Aborts on the scheduler thread are kept in `Interp.handler_exc` and re-raised when the foreign
call returns. Tests: `tests/run_callbacks.py` (a C pthread calling back), `tests/run_bindgen.py`.

## Permissions (Spec 19d)

`moxie/perms.py`: `Perms` (kinds `fs.read fs.write net.connect net.listen ffi stdin env`; `restricted`
flag; `path_ok` resolves with `realpath` against the manifest directory, `connect_ok` uses
`fnmatch` on the host, `listen_ok` takes ports and ranges), `from_manifest` (validates the
`[permissions]` table), `from_flags`, and `load_for(path, flags)` (flags, else the nearest
`Moxie.toml` with a `[permissions]` table, else unrestricted). `__main__` strips the
`--allow-*`/`--deny-all` flags that come before the file name and hands `Interp.perms` to
`make_interp` (which also empties `env` without the grant). Runtime checks: `prelude.py`
(`open_file`, `read_file`, `write_file`, `connect`, `listen`, stdin through `_inp` returning
`_DeniedIn` unless the input is in memory), `calls.py` (`Connection.open`), `ffi.make_foreign`
(abort before the program runs). Static: `effects.Needs`, a subclass of `Effects` whose builtin table
maps calls to permission kinds (`fs`, `net`, `stdin`, `env`, `ffi:LIB`); `Interp.static_check` turns
a needed kind with no grant into an error. Tests: `tests/run_perms.py`.

## Static pool tally

`moxie/tally.py` (`moxie pools FILE`; `--pools run` also prints it and calls `compare`). `Tally` collects
function definitions by name (like effects) and foreign functions that return a handle, and computes per
function a `Count` of kind -> [creation sites reached, reasons]. Reasons are `loop` (inside `for`, `while`,
comprehensions, daemons, lambdas), `recursion` (the function is in a call cycle) and `fiber` (reached through
`run`). Without reasons the number is an exact upper bound; with them it is printed `N+`. Kinds match
`moxie/pools.py`. Tests: `tests/run_tally.py`, which also runs the examples and requires that no exact count is
below the observed use.

### The closing rule (tally)

`Count` entries are `[n, reasons, kept]`. For a creation of a closable kind (`Io file`, `Io socket`, `Listener`,
`Connection`, `handle X`) bound to a name by `Assign`, `Tally.escapes(v, scope)` decides whether it leaves the
iteration or function: a `move v` (argument with `mod == "move"`, or a `Move` node) into anything but a closer
(`close` and the foreign handle closers), a `Return` mentioning `v`, a closure that mentions `v`, or `v` in the
function's tail expression. Not escaping means `kept = False`, so the loop and recursion reasons are not added
and the count stays exact. A call to a user function bound to a name and not escaping clears `kept` for the
callee's closable kinds (`release=True`). Atom, Chan, Timer, and Future are always kept. A kept creation in a
loop, lambda, daemon, or recursion adds a `problem`; `Interp.static_check` turns the problems into errors unless
`--gc` is set, and `moxie pools FILE` prints them and exits 1. Tests: `tests/run_tally.py`.

## Fiber limits and the pool header

`parser.try_decl` reads `fiber[n]` before `fn` and adds the flags `fiber` and `fiber:n`. `moxie/manifest.py` loads
the nearest `Moxie.toml` ([fibers] `limit`, `memory`, `stack`; [pools] `warn_threshold`; validated, errors exit 2)
into `Interp.manifest`. `sched.run_op` counts live fibers per function (`Scheduler.live_fibers`, decremented in
`_fiber_body`'s `finally`) and returns `Err(NO_SLOT)` at the limit (`fiber_limit`: the flag, else the manifest
default, else unlimited). `Tally` no longer merges `run` callees into the starter: it records `starts[f]`, and
`program()` walks the started functions once each, scaling their counts by `limit_of(f)`; no limit means the
`fiber` reason and a warning. `fiber_count()` is 1 plus the limits. `format_header` writes JSON for
`moxie pools FILE --header OUT`. Tests: `tests/run_tally.py`.

## Language gaps: curry checks, binary patterns, constant `requires`

`check.py` has a small constant evaluator (`const_eval`, `NOCONST`): numbers, text, booleans, arithmetic,
comparisons, `and`/`or`/`not`. `check_const_requires` runs it on a direct call of a known function whose
arguments are all constants and reports a failing `requires` as a compile error. Curry rules are shape checks
(`curry_shape`, `check_curry_call`, `check_curried_application`): parameter count, excluded parameter kinds
(`ref`, `lazy`, `using`, variadic), `uncurry[n]` with a constant n of at least 2, and the argument count of
each call in `curry(f)(a)(b)`. `Bin(...)` is parsed by `pbase.parse_bin_pattern` into `PBin(elems)` and matched
by `patterns.match_bin`: fields are read left to right over the byte values, `bits(n)` packs from the high bit,
`bytes(n)` copies, a missing or wrong byte makes the arm fail, and leftover bytes fail unless the last element
is `rest: bytes`. Tests: `tests/helper_cases.py`, `tests/run_contracts.py`.

## Building bytes and Bin coverage

`pexpr.parse_bin_build` reads `Bin(...)` in expression position (the name `Bin` followed by `(` with no space) and
desugars it to `bin_build("lit:ca|bits:4|u16be|bytes", value, ...)`, so the checker, effects, and tally see an
ordinary call. `prelude.b_bin_build` packs bits from the high bit, writes the fixed-width integers in the written
byte order, aborts when a value does not fit, and returns an `Array[Byte]`. `check.bin_cover` runs from
`exhaustive` when every arm of a `when` is a `Bin` pattern and none is a catch-all: arms without a literal, a
guard, or a field-sized `bytes(n)` give a length interval (fixed size, or size and up with `rest: bytes`), and the
first uncovered length is the error. Tests: `tests/helper_cases.py`.

## `moxie fmt`

`moxie/fmt.py` formats from the lexer's own view of the file. `Lexer.spans` lists the physical lines inside a
multi-line token (triple-quoted and raw strings, SQL bodies, block comments) and `Lexer.info` gives, for the first
line of each code line, whether it continues the one before (`cont`), the indentation its place in the indent stack
calls for (`canon`, two spaces per level), its old indentation, and the stack and bracket depth before it. The
formatter keeps two shifts: the one of the last statement start, applied to continuation lines, and the one of the
last non-span line, applied to span lines. A comment-only line takes the level of its old indentation in the stack
before the next code line, or that line's level. `format_source` lexes the result and compares the token kinds and
values with the original, formats a second time and compares, and raises `FmtError` if either differs. The command
(`fmt_main`) handles `--check` and `--stdout` and walks directories for `.mxi` and `.mx`. Tests: `tests/run_fmt.py`.

## Per-package permission ceilings

`perms.load_ceilings(path)` reads `[permissions.packages.NAME]` tables from the nearest `Moxie.toml` into
`Interp.pkg_ceilings` (name to `Perms`); `[permissions]` also takes `all = true`. `Interp.perms` is now a property:
with no ceilings it returns the program's `Perms`; otherwise it looks up the package of `cur_mod` (`mod_pkg` maps a
module env's id to the package name, filled in `load_package`) and, if that package has a ceiling, returns
`perms.Combined(program, ceiling, name)`, whose checks need both to allow. `ev_Call` sets `cur_mod = env.mod`
just before applying the callee, only when ceilings exist, so the package is the one the call is written in (a
builtin passed to `map` is attributed to the call to `map`). A refusal sets `perms.CURRENT` so `prelude.denied`
can name the package. Statically, `Interp.package_diags` follows the entry's imports through the search path,
parses each package, runs `effects.Needs` over its top level and over every function summary, and reports the
kinds the combined grants do not allow at the import line; ceilings for packages never imported are warnings.
`kind_unmet` and `unmet_needs` are shared with the program-level check. Tests: `tests/run_perms.py`.

`fmt.py` now also has `_space_line`, which works on the gaps next to operator tokens (columns come from `Tok.col`):
one space around the always-binary operators and around `+ - * / %` after a value, none before a comma and one after.
`_once(src, file, spacing)` computes each code line's new indentation in a first pass that mirrors the lexer's indent
stack (`info["after"]`), so a block opened under a continuation line goes two spaces deeper than that line. After
the line pass, a blank line is added before a top-level declaration word that follows a block. `format_source`
applies spacing only when `repr(parse_program(...))` is the same before and after; the string-token comparison
ignores the line numbers kept inside interpolations.

The lexer also records each comment's text in `Lexer.comments` (a line comment as written, a block comment with the
indentation of its inner lines removed). `format_source` compares the list before and after formatting and refuses to
write if it differs, so a comment can neither be lost nor altered.

## Directories and paths

`prelude.py` adds `list_dir`, `file_info`, `path_exists`, `make_dir`, `remove_file`, `remove_dir`, `rename_path`
(each guarded by `I.perms.path_ok` for `fs.read` or `fs.write`, and mapping `OSError` through `io_error`) and the
text-only `path_join`, `path_parent`, `path_name`, `path_stem`, `path_ext`. `FileInfo` and its `is_file`/`is_dir`
methods are declared in `mxprelude.py`; `file_info` builds the tuple directly. `effects.py` lists the seven file
system functions as `parks` and as `fs` needs, so a restricted program that reaches one without a grant is a compile
error. Tests: `tests/run_fs.py`.

## TLS

`connect_tls` and `listen_tls` in `prelude.py` use Python's `ssl`. The client builds `ssl.create_default_context()`
(or with `cafile=` from the named argument `ca`), connects on a helper thread like `connect`, and wraps the socket
with `server_hostname=host`, so the certificate and the name are always checked; `_tls_error` turns verification
and handshake failures into `IO_ERROR` messages. The server loads the certificate and key into an
`SSLContext(PROTOCOL_TLS_SERVER)` kept in `ListenerV.ctx`, and `accept` wraps each accepted socket on the helper
thread, returning `Err` for a failed handshake. The result is an ordinary `IoV` socket, so the pool tally,
permissions, and static `net` needs treat the new functions like `connect` and `listen`. Tests: `tests/run_tls.py`
(skipped when `openssl` is missing). The guide runners skip blocks that start with `// not run`.

## The pool header at start

`tally.header_dict` builds the header (version 1, `pools` counts with `null` for unknown, `fibers.largest`, and a
SHA-256 of the program's tokens, from `tally.program_hash`, so layout, spacing, and comments do not change it); `format_header` writes it for `moxie pools FILE --header OUT`. `moxie/header.py`
reads it. `prepare(I, src, name, manifest, header_flag)` runs in `__main__` before `run_source`: it picks the file
(`--header=FILE`, else `[pools] header`), refuses one whose hash is not the program's, builds the header from a tally
when only `[program] memory` is set, applies `budget_error` (largest fiber count times `[fibers]` `memory` plus
`stack` against `[program] memory`; sizes come from `manifest.parse_size`), and then sets `Pools.caps` (acquire
aborts past a count) and `Scheduler.fiber_cap` (`run` aborts when that many fibers are alive). Kinds the header
lists as `null` or does not list are not capped. Under `--gc` the options are refused, since moxie/gc has no pool
header. Tests: `tests/run_header.py`.

The tally follows imported packages. `Tally(prog, limit, search_dir)` builds a `Tally` for each imported package
(shared through `_shared`, registered before it is built so an import cycle cannot recurse) and `pk(f)` resolves a
qualified call or a name from `import p (name)` to `(package tally, function)`; `call_in(..., owner=)` then asks the
package's tally. Fiber functions are `(tally, name)` pairs, and a function's `starts` now flow to its callers, so a
helper that runs a fiber function counts toward the largest fiber count. `program()` also adds each package's top
level and merges the packages' `problems` (prefixed with the package name and file line). `program_hash(src,
search_dir, prog)` hashes the tokens of the entry file and of every package from `load_packages`.

UFCS: `x.name(...)` and `name(x)` reach the same function, so `Tally.pk_methods` adds, for a field-style call that is
not on a package alias, every `impl` method of that name in the imported packages (`Tally.methods` is the set of
names defined inside impl blocks). Like the by-name counting inside one file, this can over-count, never under-count.

## Effects and needs across packages

`Effects` and `Needs` take a `search_dir` and analyze each imported package once (`_shared`, registered before
construction so an import cycle cannot recurse), as `Tally` does. `ensure()` computes a package's summaries (and,
for `Needs`, its top-level needs) after the packages it imports. `pk(f)` resolves `lib.f` and `import lib (f)`
names, `pk_methods(f)` adds the `impl` methods of that name for UFCS `x.f()`, and `add_pkg` copies the callee's
effects into the caller and applies the effects of arguments to the callee's `param_calls`. `Needs.solve` adds each
package's top-level needs at its import line. `check_program(prog, names, search_dir)`, `permission_needs`, and
`check_effects` pass the entry file's directory through; `Interp.package_diags` builds `Needs(pp)` without it, so a
ceiling is checked against what a package's own code does. Tests: `tests/run_pkgeffects.py`.

## The moxie/gc heap limit

`moxie/heap.py` enforces `[memory] heap` under `--gc`. `model_size` walks everything the program can still reach (the
fibers' generators and Python frames, `Env` scopes, the value classes of `values.py`, `sched.py` and `streams.py`, and
plain containers), ignoring syntax trees and the interpreter, and adds 16 bytes per value, 8 per slot and a string's bytes.
`heap.tick` is called on each user call, each `for`/`while` turn and each scheduler step; every `heap_gap` ticks
(at least 4000, one hundredth of the last measurement) `check` measures, and over the limit runs `gc.collect()` and
measures again before raising `ProgramExit` with the `out of memory` summary. `header.prepare` sets `heap_limit` and
refuses `[memory]` without `--gc`. Tests: `tests/run_heap.py`.

`fmt.py` also has `_wrap` and `_break` for lines over `WIDTH` (80). They run after `_once`, using the lexer's bracket and
comma tokens (`Tok.col`, so strings are never split). `_break(text, marks, indent)` picks the outermost group that reaches
past the width (or the last one that starts before it), puts each top-level item of that group on its own line two
deeper, and calls itself on the head line, every item, and the closing line; it gives the original back when the result
is not shorter. `format_source` then checks the parse tree, tokens, comments and that both `_once` and `_wrap` are stable.

## Pool sizes in the budget

`moxie/layout.py` has the slot table (`SLOT`) and `layout(type, decls)` for the size and alignment of a type, and
`slot_bytes(kind, call, decls)` for one creation site (a `Chan` from its element type and constant capacity, an `Atom` or
`Future` from its type argument, an `Atom` from a number or `Bool` literal). The tally's `Count` carries `b` (bytes by
kind, scaled and merged with the counts) and `why` (the sites whose size is not known). `header_dict` stores
`bytes: {pools, unknown}`, `header.budget_error` adds `pools` to the fibers' need and refuses when it is `None`, and
`format_tally` prints the total. A header without `bytes` adds nothing. Tests: `tests/run_header.py`.

The checker requires a type on every plain-name parameter of a named function (`check.e_FnDecl`), as it requires a return type; later clauses of a multi-clause function, foreign declarations and aliases, and lambdas are exempt.

UDP (`prelude.UdpV`, `bind_udp`, `send_to`, `receive`): a `Udp` wraps a `SOCK_DGRAM` socket. `receive` reads up to 65535 bytes on the helper thread (so only its fiber parks) and honors `timeout:`; the `Packet` tuple is declared in `mxprelude`. It is a resource (`RES_TYPES`, `RES_MAKERS`), counts as an `Io socket` in the pool tally, has the `parks` effect, and needs `net` (`bind_udp` against `net.listen`, `send_to` against `net.connect`). `tests/run_udp.py` covers it over loopback. Not built: `select` over a socket, IPv6 and multicast, and connected UDP sockets.

`[fibers]` takes `strings` and `temps` as a division of `memory` (`manifest.fiber_spaces`); the budget in `header.budget_error` adds them and shows the split in its message. The spaces themselves are not modeled, so neither is enforced.

## Property tests (`forall`)

`forall a: T, b: U:` is a statement parsed in `parse_stmt_core` (node `ForAll(binds, body)`) and
meant for `test` blocks. `ev_ForAll` in `interp.py` makes `--cases` (default 100) argument sets with
`random.Random(f"{seed}:{line}")`, so each `forall` has its own stream and a run repeats exactly;
`--seed` and `--cases` come from `__main__` as `I.forall_seed` and `I.forall_cases`. A case that
aborts is shrunk greedily: the first smaller candidate that still fails is taken, and the search
restarts from it (at most 500 trials). The report names the case, the seed, and the shrunk input,
with the first failing input beside it when they differ.

`moxie/forall.py` holds the generators (`gen`) and shrinkers (`shrinks`). Both walk the type AST, so
a declared tuple (`I.tuples`) or enum (`I.enums`) is built from its field types, and a generic or
function type raises `NoGen` ("forall cannot generate ..."). Integers mix edge values (0, 1, -1,
the limits) into the range; shrinking moves toward 0 by halving steps, lists drop and shrink
elements, strings shorten. The checker binds the names with their declared types (`e_ForAll`), and
the effects pass reports a `forall` outside a `test` and a body that prints, parks, or has any
other effect. 
The signature rules live in `Checker.check_generatable` (check.py), so a misshapen impl never reaches the runtime. A mixer-written `Generatable` is found through `I.statics[T]["generate"]` and `I.impls[T]["shrink"]`
and takes precedence over the built-in generator for `T`, wherever `T` appears (`gen` and
`shrink_list` are generator functions so they can run moxie code). `Gen` is `GenR` in `prelude.py`
(a `random.Random`, the size, and the nesting depth); `gen_int`, `gen_bool`, `gen_pick`, and
`sample[T]` are builtins, and `sample` calls `forall.gen`. Nesting deeper than 24 raises `NoGen`.
Tests: `tests/run_forall.py`.

## The system (`moxie/system.py`, Spec 19e)

Clock, random numbers, exit, signals, and facts about the host are builtins registered from
`system.py` (imported at the end of `prelude.py`). The scheduler's clock is virtual (`sleep` jumps
it forward), so `monotonic` is the real monotonic clock plus `sched.now`, and `now` is the real
wall clock plus `sched.now`: a program that sleeps always sees the time pass. `exit` raises
`ProgramExit`, which the scheduler already carries out of any fiber. `signals()` builds a `Chan(8)`
and an `EventSink` like a C-kept `Events[T]` callback, and Python signal handlers (main thread only)
call `post_event`; `Scheduler.sig_listeners` makes an idle loop wait in real time, with a timeout at
the next sleeper or timer, instead of jumping virtual time, so a sleeping fiber and a signal can both
be served (`run_main`, `next_due`). Effects: `effects.SYSTEM` ("uses the system") is a third inferred
effect for the calls in `SYSTEM_CALLS`; `pure fn`, contracts, and `forall` bodies reject it, and a
declaration that lists only `prints` or `parks` is told to declare `impure`. `lookup_host` needs
`net.connect` for the host on any port, and `make_temp_file` and `make_temp_dir` need `fs.write` on
`tempfile.gettempdir()`. `signals` counts as one `Chan` in the tally (`layout.slot_bytes`). Tests:
`tests/run_system.py`.

## Platforms (`--platform=browser`, Try moxie)

`perms.PLATFORMS` names, per platform, a label and the `platform:` pseudo-kinds it lacks. `effects.NEEDS`
maps `signals` to `platform:signals`, so the existing reachability walk (`permission_needs`) finds it,
and `Interp.static_check` reports `'signals' is not available in the browser` when `Interp.platform`
lacks it (`kind_unmet` ignores `platform:` kinds). `Perms.browser()` grants fs, stdin, and env but
not net or ffi, with the source `the browser`, so the ordinary needs check refuses `connect`,
`lookup_host`, `bind_udp`, and foreign blocks. `moxie --platform=NAME` sets both; `docs/try-worker.js`
sets both for the page. `os_name` answers `browser` when `Interp.platform` is `browser` or
`sys.platform` is `emscripten`. The page was checked under a real Pyodide 0.26.4 core in headless Chromium
(`tests/try_page.js`, a manual script): the clock, random numbers, files, temp files, dates, tests,
the gc box, the Stop button, and the check-time refusals all behave as described. Pyodide has no
`os.get_terminal_size` (so `terminal_size` returns `Err`) and no host time zone database. Tests:
`tests/run_platform.py`.

## Running other programs (Spec 19e)

`run_command` runs `subprocess.run` on a helper thread (`park_thread`), with `stdin=DEVNULL` unless
`stdin:` is given, and the child's environment is the program's `env` snapshot unless `env:` is given
(`_prep`). `spawn` makes a `ChildV` (move-only, in `Interp.live_children`, killed at exit by
`run_source`) with stdin and stdout pipes and stderr merged into stdout; `child_stdin` and
`child_stdout` return cached `IoV` objects of kind `socket` (so they count as `Io socket` in the pool
tally and work with `read_line`, `lines`, `println`, and `close`). A negative return code is reported
as `128 + signal`. The permission kind `process` (`Perms.process_ok`, matching the program as written
or its base name; `--allow-run`; `process = [...]` in the manifest) is checked per call, and the
static needs check follows `run_command` and `spawn` (`effects.NEEDS`). `Perms.browser()` grants no
`process`. Tests: `tests/run_process.py`.

## Dates and times (Spec 19e)

`DateTime` is a prelude tuple in `mxprelude.py` (defaults for the time fields); `system.py` builds
and reads it as a `TupleV` named `DateTime`. Conversions use Python's `datetime` and `zoneinfo`
(`to_utc`, `to_local`, `to_zone`, `to_instant`; a nonexistent local time is reported by `_valid`,
an ambiguous one takes the first, as `fold=0` does). `format_time` and `parse_time` are our own code
for a fixed set of codes (`_format`, `_parse`), so the output does not depend on the C locale; month
and weekday names are English. `parse_iso` tries a list of patterns and refuses an offset. Only
`to_local` is in `effects.SYSTEM_CALLS`. Zone names come from the host's database (Python's `zoneinfo`), then from the copy in
`moxie/zoneinfo/` (copied from a system tz database; names are matched against a strict pattern, so
a name cannot climb out of that folder), and otherwise the zone functions return `NOT_FOUND`. A
browser has no host database, which is why the copy ships. Tests: `tests/run_datetime.py`.

## Raw terminal input (moxie/terminal.py)

`raw_terminal()` saves `termios.tcgetattr(0)` and clears ECHO, ICANON, ISIG, IEXTEN and the input translations (ICRNL, IXON, ISTRIP, INPCK, BRKINT) with VMIN 1; OPOST is left on so `\n` still returns the carriage. The `TermV` handle is added to `I.live_children`, so the same cleanup that kills spawned programs at exit also restores the terminal, including after an abort. `read_key` runs `_decode` on an OS helper thread (`park_thread`) reading bytes with `os.read(0, 1)`; `_decode(get, ready)` is pure over a byte source so the tests drive it directly. A lone ESC is told from a sequence by `select` with a 50 ms wait. The `Key` enum is declared in mxprelude.py; the builtin builds a case with `I.enum_instance`. `tests/run_terminal.py` runs programs under a pty and checks the restored `lflag`.

## Unix sockets and named pipes (moxie/pipes.py)

`listen_unix` binds an `AF_UNIX` stream socket and returns a `UnixListenerV`, a `ListenerV` that unlinks its path when dropped and is on `I.live_children`, so exit and abort remove the file. `connect_unix` connects on a helper thread and wraps the socket in a `"socket"` `IoV` exactly as `connect` does. `make_fifo` is `os.mkfifo` (mode 0600). `open_file` checks `is_fifo(path)` and, for a FIFO, opens it on a helper thread because the open waits for the other end; the result is an ordinary `"file"` `IoV` around a `PipeR` or `PipeW`. `PipeR` keeps its own buffer and waits with `select` in 100 ms slices, so a read that is still waiting notices `close` and a program can exit without joining it (a buffered Python file would deadlock closing under a blocked reader). There is no anonymous in-process pipe: the scheduler does not advance virtual time while an OS wait is pending, so two fibers joined by a pipe and a `sleep` could hang, and channels already cover fibers. `tests/run_pipes.py` covers it.

### Sleeping while an OS call is in flight (2026-11-05)

`run_main` used to wait for every helper-thread call before advancing virtual time, so a `sleep` or timer in another fiber stood still during a socket, pipe, or child wait and a watchdog fiber could never fire. Now, when a call is in flight (or a `signals()` channel exists) and a sleeper or timer is due, the loop waits on the helper queue in real time for at most the time to the next due one, adds the elapsed real time to `sched.now`, and advances when it is reached (the branch that already served signals). With nothing in flight the clock still jumps, so programs without outside waits stay instant and deterministic. The exception for a handler fiber with sleepers is kept.

## Ownership checking (check.py)

`Checker.find_consumers` computes, before the walk, `consumes[name]` = the positions of resource parameters a single-clause function keeps: its body has `close(p)`, `p.close()`, a foreign closer call on `p`, `Move(p)`, an argument written `move p`, `return p`, or `p` as its last expression. `check_hand_over` then rejects `f(c)` where `c` is a resource variable passed (by position or label) to such a parameter without `move`. `f(move c)` is an `Arg` with `mod == "move"`, not a `Move` node, and used to be ignored, so the name was never marked moved; `_move_name` (shared with `e_Move`) now marks it, which gives use-after-move and the move-in-a-loop error. Tuples that hold resources, methods, and multi-clause functions are not analyzed. `tests/run_moves.py` covers it.

### The event queue is a SimpleQueue (2026-11-05)

`Sched.extq` was a `queue.Queue`. A Python signal handler runs on the main thread between bytecodes, so it could fire while the scheduler was inside `extq.get()` holding the queue's (non-reentrant) mutex; the handler's `post_event` then called `put`, which waited for the same mutex, and the program hung forever. It showed up as the signals test failing about one run in six. `queue.SimpleQueue` is written for this case (its `put` is reentrant and takes no lock a `get` holds), so signals, foreign callbacks, and helper-thread results all use it. `tests/run_system.py` sends 300 signals in a burst to catch a return of the bug.

### Ownership: tuples, methods, close (check.py)

`res_tuples` is the closure of "a tuple with a resource field". `is_res_type` covers built-in resources, foreign handles, and those tuples; `is_resource_expr` also recognizes tuple constructors and user functions that return a resource (or a `Result`/`Option` of one under `?`). `find_consumers` now covers every clause of a function (the union of positions), a closed or moved field of the parameter (`close(p.io)`, `move p.f`), and methods: `method_consumes` holds `(Type, name)` for methods that keep `self`, found from `ImplDecl` members. `close(x)`, `x.close()`, and `x.f()` where `f` keeps its first parameter (or `x`'s static type has a method that keeps `self`) mark `x` moved after the call has been checked (`pending_gone`, applied by the `e_Call` wrapper, so the call's own receiver is not reported as a use after the move). `collect_moves`, which merges moves across branches, understands the same forms. `check_stored` requires `move` when a resource variable goes into a tuple constructor. The receiver's type comes from `Var.ty`, which the checker only knows for a few forms, so an untyped receiver is not analyzed (a missed error, never a false one).

## Future backends (plans, nothing built; discussed 2026-11-05)

The reference interpreter walks the tree (`ev` dispatches on node class; fibers are generators the scheduler resumes). Two plans for compiled backends are on record. They are not exclusive, and no choice has been made.

### Plan A: moxie/gc to Python, then moxie to WebAssembly (agreed first)

1. **moxie/gc to Python.** Generate Python `ast` objects from the checked program and `compile()` them, rather than writing bytecode (bytecode changes between Python versions). Python is garbage collected, so this is a faithful gc backend; for the no-GC dialect it could only model the limits, so it should be labeled as the gc backend. Start with functions, `when`, loops, and tuples; compile any function that can park (the effect analysis already says which) into a generator and the rest into plain functions; then add the runtime checks the tree-walker does now (pool limits, closed-resource errors, bounded-integer overflow, abort messages with lines, contracts). Keep the tree-walker as the reference and run every suite and example through both, comparing output.
2. **moxie (no GC) to WebAssembly.** The one-block layout the Spec describes (static region, module storage, resource pools, one stack block per possible fiber) maps onto linear memory. Open questions: fibers need their own stack switching or compilation to state machines, and files and sockets come through WASI.
3. **Later, if wanted:** the JVM for moxie/gc (virtual threads suit fibers; no tail calls, so `tailrec` becomes a loop).

### Plan B: WebAssembly for both dialects (raised later the same day)

One backend for both dialects would run wherever WebAssembly runs (browsers, servers, embedded runtimes) and could replace Pyodide on the Try page. Points to settle:

* **The "native code" promise.** WebAssembly is a portable binary format that a runtime turns into machine code, close to native speed but not literally "no bytecode". The site intros say moxie "compiles straight to machine code, so there's no bytecode standing between you and the hardware". That holds literally only with an ahead-of-time compiler (Wasmtime-style); otherwise the wording changes, for example to "compiles to WebAssembly, which runs at near-native speed". A wording decision for Steve when a backend exists.
* **moxie (no GC)** is the clean fit: it lays out its own memory in one block.
* **moxie/gc** needs a collector: use the host's WebAssembly garbage collection where available (reported as supported in the major browsers; verify before relying on it), or ship a collector inside linear memory, which works everywhere and costs more.
* **Fibers** are the hard part for both: no coroutines in the core instruction set, so each fiber needs its own stack (stack switching, where hosts offer it) or compilation of parking functions to state machines.
* **The Python step.** Under Plan B the Python backend is no longer a deliverable. It is an optional first spike for learning how to structure a compiler (one pass over the checked tree, effects deciding which functions become generators), and that structure carries over. It can also be skipped.

Either way the tree-walker stays as the reference, and every suite and example runs through both for comparison.

## File watching (moxie/watch.py)

`watch(path)` makes a `Chan` of 16 (counted in the pool tally and given a fixed slot estimate in `layout.slot_bytes`), an `EventSink` like `signals` uses, and a daemon thread that sleeps 100 ms, scans, and posts `FileChange` tuples for each difference through `post_event`. The scan is `os.stat` for a file or `os.scandir` for a directory (non-recursive; a subdirectory's stamp is the constant `("dir",)` so only creation and deletion show). `sched.listeners` and `sig_listeners` are raised so an idle program waits in real time and sleepers keep time. When `chan.rcount` drops to 0 (the reader was closed) the thread posts `WATCH_STOP`, and `deliver_event` lowers both counts on the main thread, so a closed watcher no longer hides a real deadlock. A polling design was chosen over inotify, FSEvents, and ReadDirectoryChangesW to stay portable and dependency-free; a native backend could replace `_scan` and the thread without changing the language. `tests/run_watch.py` covers it.

## Structured concurrency and cancellation (sched.py)

`Cancel()` makes a `CancelV` (a flag and a `sel` list of fibers waiting in a select); `cancel(c)` sets the flag and calls `notify_sel(c)`. The `cancelled(c)` select arm is ready when the flag is set and registers the fiber in `c.sel` otherwise, exactly like `closed(ch)`.

`scope:` / `scope NAME:` is the `ScopeE` node. Each `Fiber` has a `scope` slot. `Sched.spawn` gives a new fiber the spawning fiber's current scope and counts it in `scope.live`; `finish` and `abort` call `leave_scope`, which decrements the count and wakes the waiting owner at zero. Because children inherit the scope, grandchildren are counted too. `scope_op` swaps `f.scope` for a new `ScopeState` while the body runs and restores it in a `finally`. On a normal end it joins (parks with `("block",)` until `live == 0`). On `ReturnEx`, `BreakEx`, or `ContinueEx` (which is how `?` leaves a function) it sets the token, wakes selectors, joins, and re-raises. `Abort` and `ProgramExit` pass through untouched, so a fiber abort still ends the program. The scope's own token is not counted in the pools, since the block makes one per run; `Cancel()` is, and cannot be created in a loop.

Tests: `tests/run_concurrency.py`.

## Built-in packages: fp.state (moxie/std, moxie/stdpkg.py)

Packages the interpreter ships are ordinary `.mxi` files under `moxie/std/` (so `fp.state` is `moxie/std/fp/state.mxi`). Each of the three package finders (`decls.load_package`, `effects.find_package`, `tally.find_package`) looks in the program's own directory first and then falls back to `stdpkg.find_std`, so a program's own `fp/state.mxi` wins. `stdpkg.GC_ONLY` lists the packages that only moxie/gc has; the loader aborts and the checker reports an error when one is imported without `--gc`. `fp.state` is the State monad from the gc Guide (24h) plus `get`, `put`, `modify`, `gets`, `eval`, `exec`, and `traverse`; `traverse` is a tail call because loops carry values forward and can't build a result by reassigning an outer name. Tests: `tests/run_fpstate.py`.

## Running with no file named (__main__.default_entry)

`moxie run`, `check`, `test`, `pools`, and `doc` with no file (or a first argument that is neither a `.mxi`/`.mx` name nor an existing file) use `entry` from `./Moxie.toml`, else `./main.mxi`, and the argument stays a program argument. Tests: `tests/run_entry.py`.

## Packages of several files, visibility, and moxie doc scopes (packages.py, doc.py)

`packages.package_files(search_dir, parts)` is the one place that finds a package: `a/b.mxi`, then `a/b/Moxie.toml` with `files`, then `a/b/b.mxi`, then `moxie/std`. The loader runs a multi-file package's files in order in one module env, so `internal` names are shared between its files; the other consumers (effects, tally, the native-library check, the pool-header hash) join the files into one program with `packages.parse_package`. Importers only see `export` names (`internals` keeps the hidden ones for the error message), and `check.check_package_access` reports `pkg.name`, `pkg.Type` in a type position, and `import pkg (name)` of an internal or file-local name at check time. `moxie doc` documents a top-level binding when it is exported, internal, or has a doc comment (kind `value`).

`moxie doc` builds `Unit`s: a file, one package (all its files), or with `--all` the target plus every imported package (`--std` keeps the built-in ones). One unit prints or writes `index.*`; several write an index plus a page per unit. Examples run against the unit's joined source (repeated `import` lines kept once). Tests: `tests/run_packages.py`.

### `run` moves its resource arguments (check.py e_RunE)

`run f(x)` and the short form `run fn (x): ...` mark each named resource argument as gone (`mark_gone`), because the interpreter hands the object to the fiber (`Fiber.owned`) and drops it when the fiber ends. Reusing the name afterward is "use of moved value", and doing it inside a loop is the usual "gone the next time round" error, so a second fiber takes `clone(x)`. A `run` that returns NO_SLOT drops the arguments it was given (in `run_op`), as if the fiber had started and ended at once; otherwise the handles would leak and a reader would deadlock. Tests: `tests/run_moves.py`, `tests/run_tally.py`, `tests/run_udp.py`.

## Grapheme clusters (moxie/graphemes.py)

`graphemes(s)` and `grapheme_count(s)` apply the UAX #29 extended-cluster rules (CR LF, Hangul jamo, Extend/ZWJ/SpacingMark, emoji ZWJ sequences, regional-indicator pairs) to properties taken from `unicodedata`. Extended_Pictographic is approximated by the emoji blocks, and the Unicode 15.1 Indic conjunct rule is not applied (so "स्ते" is two clusters). Tests: `tests/run_graphemes.py`.

## Secret[T] (moxie/secret.py)

`SecretV` holds the value; `__str__` and `__repr__` give `Secret(***)`, so show, interpolation, print, and dbg are all redacted, and `__eq__`, ordering, and `__hash__` abort. `secret_eq` uses `hmac.compare_digest` on the UTF-8 bytes. The checker knows the type `("secret",)`: `secret(x)` and `Secret[T]` produce it, comparing one is a compile error, and passing a `String` where a `Secret` is expected (or the reverse) is a type mismatch. `layout` gives a `Secret[T]` the size of `T`. Tests: `tests/run_secret.py`.

## Dict key size warning (check.check_key_sizes)

A `Dict[K, V]` or `Set[T]` written in the program whose key type has a fixed `layout` size above 64 bytes (`[program] key_warning` in the manifest changes it; 0 turns it off) gets a warning at check time. Types with no fixed size (`String` without a capacity, lists) don't warn. Tests: `tests/run_keywarn.py`.

## The resource effect (effects.py)

`RESOURCE` ("uses a resource") joins parks, prints, and system. `RESOURCE_CALLS` (Chan, Timer, after, Future, Cancel, Atom, clone, close, arm, arm_every, disarm, resolve, reject, cancel, swap, reset) and the `@` read (`Deref`) have it, and it travels through callees and parameters like the others. Like "uses the system" it has no keyword: a declared non-empty set needs `impure` to cover it, and an `impure` upper bound allows it. Tests: `tests/run_effects.py`.

## Locale (moxie/locales.py, mxprelude.py, system.py)

`locales.py` holds the data (separators, date order, names) for en_us, en_gb, de_de, fr_fr, es_es. The `tuple Locale` declaration with English defaults is generated from it (`tuple_source()`) and appended to the prelude source; `mxprelude.install` then builds `I.locales` (the `Locale.de_de` values). `calls.apply` records `I.call_env` before a builtin runs so `system._loc` can reach `find_locale` (the `using` in scope). `_format` and `_parse` take the locale's names; `%x` and `%X` expand to the locale's date and time patterns first. An explicit Locale third argument to `format_time`/`parse_time` wins.

## Memoization (tests/run_memo.py)

No prelude function: the Guide (chapter 14) shows the recipe, an `Atom` holding a `Dict` that a function consults before computing, and `run_memo.py` keeps it working.

## Generics in the checker (check.py: check_op_bound, generic_call, check_type_arity)

Inside a generic function, a parameter typed exactly `T` is recorded in `tp_vars`; an operator on it needs a matching prelude bound (`OP_NEEDS`), unless the parameter has a `where` clause or a user interface bound (which may embed what is needed). A call binds each `T` from the arguments whose parameter is exactly `T`: two different types are an error (Int, Float, and Decimal may mix), and a result typed `T` takes the bound type when it is not numeric. `check_type_arity` compares the number of type arguments with the parameters of a declared tuple or enum (types with holes are skipped). Not yet covered: bounds on method calls, nested signatures such as `List[T]`, higher-kinded parameters.

## List monad, monad packages, and type arguments at run time (mxprelude.GC_SRC, std/fp/*.mxi, calls.py)

`mxprelude.GC_SRC` adds `impl Monad[List[_]]` when running moxie/gc, so list methods and `for:` give lists (an impl method wins over the stream stage of the same name). `fp.reader`, `fp.writer`, `fp.cont`, `fp.free`, and `fp.trans` are written in moxie under `moxie/std/fp/` and are gc-only (`stdpkg.GC_ONLY`).

Transformers need the inner monad's `pure`, which the interpreter cannot guess from a value, so type arguments travel at run time:
- A type value keeps its arguments (`TypeV.args`, from `targ_value`; a bound type parameter such as `M` is looked up in the environment).
- A static member called on a type value, `StateT[Result[_, E], Int, _].pure(x)` or `M.get()` with `M` bound to that type, binds the impl's own type parameters from those arguments (`calls.bind_impl_targs`).
- A generic tuple built where the expected type is written out (a function's return type, `StateT[M, S, B]`) remembers its arguments in `TupleV.targs` (`decls._construct_hinted`); a method called on such a value binds the impl's type parameters from them (`calls.bind_receiver_targs`, run from `try_bind`), and `types_.value_targs` hands them on when a type parameter is inferred from a value.
A value built where nothing names the type (a bare `StateT(run: ...)` in a lambda) carries no arguments; the library's own constructors always do, so users who build stacks through `M.pure`, `M.get()` and the `lift_` functions never meet the gap.

`fp.trans` also has `ContT` with `MonadCont`, `FreeT` with `MonadFree`, and `listen`/`censor` on `MonadWriter`. A transformer value built by a bare constructor inside a lambda has no `targs`; where a later `flat_map` needs the inner `pure` (`FreeT`'s `FtMore` branch, `ExceptT`'s `Err` branch), the library builds it in a nested `fn` that names its return type (`FreeT.wrap`).

## Type lambdas (typelam.py, pbase.parse_type_prim, calls.targ_value, check.py)

`[A] -> T` parses to `TLambda(params, body)` (`TApp` for `([A] -> T)[Int]`); params use the constructor-parameter syntax, and a kind may nest (`T[_[_], _]`). `typelam.subst` replaces parameters by types (an applied constructor parameter `M[A]` is reduced with `apply_ctor`, which fills a hole or beta-reduces a lambda); `as_ctor` turns a lambda into the constructor its body names, parameters as holes. At run time `calls.targ_value` accepts a lambda, a generic alias (`alias_tps` keeps the alias's TParams), and an alias applied to arguments, closing over bound type parameters first (`close_type`), then builds the usual `TypeV` with arguments, so static members (`M.pure`) work through it. `ev_GenApp` makes `Alias[Args]` a type value. An `impl` whose target is a lambda is an impl for the lambda's head type (`ev_ImplDecl`), which is how `MonadTrans` is written. `_` in explicit type arguments leaves a parameter to inference. The checker reports the wrong number of arguments to a lambda or alias, repeated parameters, and a constructor argument of the wrong arity for an `F[_]` parameter. There is no recursion and no matching on types; TYPE-LEVEL.md has the analysis.

## Types in the checker (moxie/tys.py, check.py: ty_of_type, app_type, compat, generic_tuple, structured_call, collection_ctor)

The checker's types were scalars, bounded ranges, and declared names; a generic value was "unknown", so `b: Box[Int] = Box(v: "x")` passed. `tys.py` adds `("app", head, args[, size])` for `Box[Int]`, `List[T]`, `Result[A, E]`, and `Array[T][N]` (the size only when it is a constant), `("fn", params, ret)`, `("tup", items)`, and `("param", name)`. `compatible`, `subst`, `join`, and `unify` are pure functions; unknown (`None`) and parameters match anything, so a type the checker cannot work out never gives an error. Sources of app types: annotations (`ty_of_type`, generic aliases by substitution), constructors of generic tuples (`generic_tuple` unifies field types with the arguments), `List/Array/Set(...)` (`collection_ctor`: one element type, an Array's size is the argument count), `Ok`/`Err`, calls of generic functions (`structured_call` unifies parameters, reports a clash, and substitutes into the return type), and field access on `Box[String]`. A variadic parameter is an `Array` (a `List` in moxie/gc) inside the body. A tail expression that is a name or a call of names and literals is now checked against the return type. Function types and numeric widening are lenient; `tests/run_ctypes.py` covers it.

Step 2 (inference at calls): `_e_Call` plans the arguments of a call to one known declared function (`arg_plan`): it unifies each argument's type with the parameter type as it goes, and hands a lambda argument the parameter's function type with what is bound so far (`lam_expect`), so `app2(3, (n): n + 1)` gives `n` the type `Int` and the lambda's result fixes `U`. A lambda has the type `("fn", params, result)` (its result only when its body is a single expression). Constructor parameters are modeled too: `F[A]` in a signature is `("appv", "F", (A,))`, unification binds `F` to `("ctor", head, fixed)` (the leading arguments of the matched application, so `Result[String, _]` works), and the result type substitutes it back. A type lambda written as a type (`([A] -> Result[A, String])[Int]`) is reduced by `typelam.reduce_app` before conversion; a generic alias already was. All of it is one pass over the source in source order. Function types compare only when their arities agree. Prelude builtins still have no signatures, so a call such as `map(xs, f)` is unknown.

Builtins: `Checker.BUILTIN_RET` gives the result type of builtins whose result does not depend on their arguments (`len`, `trim`, `starts_with`, `is_ok`, `sqrt`, `show`, and a few more); a user function or method of the same name wins. A builtin that works on several kinds of value (`upper` on a String or a Char, `floor`) is left out until the checker has overloads, and the rest of the 258 are still unknown.

Overloaded builtin signatures (moxie/sigs.py, check.py: load_sigs, sig_overloads, sig_args, tys.match): `sigs.SRC` writes the headers of common prelude functions as moxie declarations in the real argument order (`map(f, xs)`: stages take the function first and the source last), with `Seq[T]` for any List, Array, Set, Ring, or Stream, and several headers for one name (`map` over a Seq gives a Stream, over a Result gives a Result; `upper` of a String or a Char). A call uses a header only when exactly one fits the argument types known so far, so an unknown argument, or a user type with its own `map`, leaves the call unknown and never gives an error from the signature alone. The arguments that are not lambdas are evaluated first so a lambda is given parameter types from the one header that still fits; a piped value or a method receiver of known type (`xs.map(f)` is `xs |> map(f)`) fills the slot the builtin's position says. This covers `map filter take drop take_while drop_while enumerate zip sort sort_by reverse reduce collect sum product count any all find first last partition unzip upper lower abs`; adding a name is one line.

Signatures, second pass: `sigs.SRC` now has 114 names (of the 258 in the prelude) with 133 headers: numbers (`abs min max clamp pow floor ceil round checked_* wrapping_* saturating_*`), text (`chars graphemes pad_* split join replace_text contains`), dictionaries and lists (`keys values items get get_or`), the rest of the stream stages and terminals (`scan chunks windows group_by span split_at zip_with min_by max_by flatten distinct cycle intersperse take_last iterate`), Result helpers (`map_err map_ok or_else unwrap ensure`), atoms (`swap reset`; `Atom[T](v)` is typed too), paths and files, printing (`println print eprintln eprint dbg trace`), and a few time and random functions. Where several overloads fit because a number converts (`abs(3)` fits the Int and the Double header), the one that fits exactly wins; where they all give the same type (`contains` is a Bool) that type is used. The rest are left out on purpose: constructors (`List`, `Dict`, `Chan`), calls with explicit type arguments (`cast[T]`, `secret[T]`, `sample[T]`), anything whose result differs between moxie and moxie/gc (`put`, `remove`, `clear`, `copy`, `list_dir`), and handles and sockets whose types the checker does not model (`connect`, `listen`, `spawn`, `read_line`). `tests/run_sigs.py` runs one sample per header with its declared type, so a header that gives a type the interpreter does not produce fails, and checks that the checker sees each result as that type.

Generic bodies (rigid type parameters): inside `fn f[T](...)`, a value of type `T` has the type `("rigid", "T")`, which fits only itself, so `fn bad[T](x: T) Int: x` and `fn bad[T](x: T) T: 1` are errors where the function is defined, once, whatever it is later called with. (A callee's own parameters stay `("param", n)`: unification binds them at each call, and binding one to the caller's rigid `T` is fine.) This is the way the Spec's rule reads, "the body may use only what the bound provides", so there is no second check of the body for each instantiation: the signature and the bounds are the contract, and an error in a body is reported at its own line instead of at a call. A literal is not a `T`, so `fn zero[T: Numeric]() T: 0` is now an error; write it with what the bound gives (`T.one() - T.one()`). Size parameters are not covered.

Members of a type parameter and calls that fit no signature: `x.m` where `x` has the type `T` must be a member of one of T's bounds (`iface_members` reads the interfaces of the program, with the ones they embed) or a function that takes `x` (`x.m()` is `m(x)`); otherwise it is an error ("`shout` is not provided by the bound of `T` (Speaker)", or "`T` has no bound, so `name` is not available on it"). A built-in bound (`Numeric`) or one from another package makes the checker stop, since it can't list their members. A call of a prelude function whose argument types are all known (no unknown part, no type parameter, no user type) and that fits none of its headers is an error that shows the argument types and what the headers take (`filter can't take ((Int) -> Int, List[Int]); it takes ((T) -> Bool, Seq[T])`).

## Type functions (tys.py: tmatch, subst, REDUCER; check.py: tfun, reduce_tapp, check_tfun_decl; parser.parse_type_match)

`type alias F[T] = when T:` with `pattern -> type` arms parses to `TMatch(scrut, arms)`. The checker turns it into a type function (`tfun`) built once, on first use: the scrutinee, and per arm a pattern and a result in `tys` form. In a pattern, a bare name that is not a known type and not a parameter of the alias is a pattern variable (`("pvar", n)`); `_` is None (matches anything); a tuple pattern may end its items with `...Rest` (`("spread", t)` inside `("tup", items)`); a size can be a variable (`Array[X][N]`); a number is `("lit", n)`. `tys.tmatch` returns "yes" (with the bindings), "no", "unk" (the type is not known), or "sym" (it is a type parameter or an unreduced function). `Checker.reduce_tapp(name, args)` tries the arms in order: yes gives the result with the bindings substituted (a result that names a type function reduces in turn; `subst` calls `tys.REDUCER`), no goes on to the next arm, unk gives unknown, sym leaves a symbolic `("tapp", name, args)` that fits only itself, which is how `Elem[T]` behaves inside a generic function and why it reduces at the call, once unification has bound `T`. No arm matching is an error at the use. The limits are `TF_FUEL` (64 reductions in one use, counting the nested ones) and `TF_MAX_NODES` (4,000 nodes in an argument, counted as a tree with a memo so a type that doubles at every step is caught at once). `check_tfun_decl` warns about a self-call whose arguments hold no pattern variable from inside the arm's pattern (a "piece" of what was matched) and no size step. Numbers: an arm result or pattern can be a number or arithmetic (`parse_arm_result` falls back to an expression, `type_num` converts it), `+ - *` fold when both sides are numbers, and `size_term` lets a type function that gives a number stand where a size goes. Arrays carry their size as the fourth item of `("app", "Array", args, size)`. Not covered yet: guards on arms (`if`), matching on a function type without parentheses, unions in patterns, bounds on pattern variables, and nothing of this at run time: the interpreter parses these aliases and ignores them, so they are checked, not enforced by `coerce`. `tests/run_typefun.py` covers it.

Type functions, second pass: arms may have a guard (`pattern if cond -> result`; the parser keeps arms as `(pattern, result, guard)`). `eval_guard` evaluates it under the arm's bindings with three-valued logic (True, False, or "sym"/"unk" when a type it needs is not known, which leaves the application symbolic or unknown like a failed match): `and`, `or`, `not`, and `== ~= < > <= >=` on numbers (`("lit", n)`) and on types (structural equality). A string in quotes is a type, `("slit", s)`; it matches by equality, `+` joins two at the type level, and it is compatible with `String` where a value is checked. Not done: inferring a singleton type from a value argument (a call `get("name")` does not make `K` the type `"name"`, so a function that takes the key as a value can't select its result type from it yet). The reduction limit is `[program] type_fuel` in `Moxie.toml` (default 64), read in `manifest.py` and passed to `check_program`.

Type functions, third pass: labels and singletons. A tuple type is `("tup", items[, labels])`; labels are ignored by `compatible`/`unify`/`join` (a tuple is checked by position) and used by `tmatch` (`_label_match`: a `("pvar", n)` label binds the field name as a `("slit", name)`; a string type must equal it). `check.tuple_label` turns a label into `("param", n)` (an alias parameter) or `("pvar", n)` (a pattern variable) while a type function is being read (`in_tfun`). `subst` carries labels along, splices a spread tuple's labels, and resolves label variables through the bindings. `tys.UNFOLD` (`check.unfold`) lets `tmatch` read a declared tuple (`named`/`app`) as its labeled fields. `e_StrLit` returns the text as its constant when it has no interpolation, and `structured_call` binds a bare type parameter to `("slit", text)` / `("lit", n)` from a literal argument only when that parameter appears inside a type-function application (`tapp_params`); otherwise the argument is widened as before.

Type functions, fourth pass: `X: Iface` patterns. The parser reads a NAME, `:`, NAME at the start of an arm as `TBound`; `ty_of_type` gives `("bound", ("pvar", X), iface)`; `tmatch` asks `tys.IMPLEMENTS` (`check.implements`): True binds the variable, False is no match, None is unknown (the application stays unreduced).

## Compile-time evaluation (cteval.py; check.py: CT, const_eval, fold_binding)
`CtEval` builds a second `Interp` (output discarded, `Perms.none()`) from the program's fn/tuple/enum/alias/iface/impl declarations and runs `name(args)` for a function the effect analysis finds pure. Every `disp` entry is wrapped to count steps; `eval_fuel` (default 200000) ends the run, and Python's RecursionError is reported as "recursed too deeply". `const_eval` gets a `Call` case through the module hook `CT`; `const_int`, `size_expr`, `type_num` and `size_term` use it, and `fold_binding` records top-level constants in `Checker.consts`. Aborts and limits are collected in `CtEval.errors` and added to the diagnostics. Results are Python int/float/bool/str only. Not done: a call whose argument is a type variable (a guard such as `N if big(N)`), which would need a symbolic call node.

Associated types in the checker: `collect` records `(type name, member) -> written type` from each impl's `type Item = ...` (`Checker.assoc`). `ty_of_type` reads a two-part path `X.Item`: a concrete `X` gives the impl's type at once (`assoc_of`); a callee parameter, rigid parameter or pattern variable gives the symbolic `("tapp", "@Item", (base,))`, which `reduce_tapp` resolves when the base is known and `show` prints as `C.Item`.

Per-value member types (check.py: any_params, any_vars, any_member_call, any_fn_result; tys 'hid'): at function entry a parameter typed `any I` gets the key `name@line`; `a.Item` in a type of that function is `("hid", key, "Item")`, equal only to itself (`compatible`, `show` prints `a.Item`). `any_member_call` types `a.m(args)` from the interface member (an associated-type result or parameter becomes the hidden type) and checks arguments; `simple_tail` lets a tail call on an `any` parameter be compared with the result type. `any_fn_result` ties `f(a)`'s result `c.Item` to the argument's own hidden type when the argument is a named `any` parameter. Not tracked: values with no name, `any` locals, function types.

`any` locals: `bind_any_local` (called from `e_Assign`) gives `x: any I = ...` the key `x@line`, or shares the key of an `any` parameter or local when the value is a plain name (`y = a`).

Guards that call functions: `type_num` turns a call into `("cfn", name, args)` with `tys.subst_partial`; `tys.subst` runs it through `tys.CALLER` (`check.type_call`, which uses `CtEval`) once every argument is a number or string, giving `("lit", n)`, `("slit", s)` or `("bool", b)`; until then it is symbolic (`_stuck` says "sym"). `eval_guard` has a `Call` case. A call that gives `Err` is recorded in `CtEval.warnings` and shown as a warning. The no-arm error names the outermost application (`tf_trail[0]`).

Intersections: `TAny` and `TBound` carry `also` (the further interfaces of `A + B`); the parser reads `any A + B` and `X: A + B`. The checker's `any` key holds a tuple of interface names (`any_names`); `any_member_call` looks a member up in each; `check_any_args` reports a known argument type that lacks an interface; `tmatch` of a `bound` pattern needs every interface. The interpreter ignores the annotation.

Signatures, third batch: `trim`, `starts_with`/`ends_with` (String or Char), `char_count`, `grapheme_count`, `path_join`, `is_ok`/`is_err`, `is_nan`/`is_inf`/`is_finite`, `sqrt`, `cwd`/`hostname`/`os_name`/`temp_dir`, `home_dir`, `list_dir`, `path_exists`, `remove_dir`, `rename_path`, `now`, `monotonic`. Not given a signature on purpose: `len` (it also takes tuples), `put`/`remove`/`clear` (the result differs between moxie and moxie/gc, and the signature table is shared), `hash`, `show`, and the network, process and terminal families, whose argument types are resources the checker does not model.

Package syntax errors: `Interp.package_syntax_diags` (called from `static_check`) parses every imported package and reports a `MoxieSyntaxError` as an error at the import, with the package file, line and column; `run_source` also catches a `MoxieSyntaxError` raised while an import runs (the `--no-check` path) and prints it with exit code 2, so neither path shows a Python traceback. `tests/run_pkgerr.py` covers check, run, and run with the check skipped.

Dialect-aware signatures: `sigs.SRC` is shared, `SRC_MOXIE` and `SRC_GC` hold the functions whose result differs (`put` gives a Result in moxie and the collection in moxie/gc). `Checker._sigs` is keyed by `GC[0]`, so each dialect reads its own table once. `remove` and `clear` are the same in both and live in `SRC`. Tests: `tests/run_sigs_dialect.py`.

Compile-time evaluation across packages: `CtEval.key_of(fn)` names a callable pure function (`big`, or `mathx.big`) using the effect analysis of the entry file and of each imported package (`Effects.pkgs`, `Effects.imported`); the sandbox interpreter runs the entry file's `import` statements too and evaluates the callee as a `Name` or `Field` node. Keys of the form `alias.name` appear in `cfn` nodes and error messages. Tests are in `tests/run_cteval.py`.

Signatures, fourth batch: `len` (String, Seq, Dict; a tuple is let through in `sig_args` because `len` counts its fields), time parsing and conversion (`parse_iso`, `parse_time`, `to_instant`, `to_utc`, `to_local`, `to_zone`), `listen`, `spawn`; `hash` joins `BUILTIN_RET`. The stale `path_exists` and `home_dir` entries of `BUILTIN_RET` (they give a Result, not a Bool or a String) were removed. Still without a signature: the calls whose arguments or results are resources the checker has no type for (`connect`, `accept`, `wait_child`, `read_key`, `raw_terminal`, and the like) and calls that take named arguments (`run_command`), because the signature path does not read labels.

## Properties (tests/run_props.py)

`property` is parser sugar plus a few hooks. `Parser.parse_property` (parser.py) reads the header (`lazy`/`static` modifiers, `property[n]`, `name: Type`, `= default`), then the accessor lines (`get`, `set(v)`, `priv set`, `will_set(new)`, `did_set(old)`; the lexer lets an indent follow a `property` line with no colon), and builds a `PropertyDecl`. `field` in an accessor body is renamed to the property's own name (`_subst_field`), and the property has storage unless it has a `get` body that never mentions `field`. A stored property also adds a `FieldDecl` (its `prop` attribute points back); `TupleDecl.props` lists all of them. `expand_props` writes the hidden methods `__get_NAME`, `__set_NAME` (a `ref` receiver), `__will_set_NAME`, `__did_set_NAME` into an inherent `impl` that `parse_stmts_until_dedent` puts right after the tuple (a lazy property's getter is a `pure fn`, so the existing effect analysis checks it; a static property's is a `static fn`). Nothing else in the checker or interpreter sees those methods except the hooks below.

Run time: `prop_of`, `prop_read`, `prop_set` (calls.py, places.py). `field_get` and `recv_member` call a custom or computed getter, except inside that property's own accessors (`accessor_prop(env.func)` looks at the hidden method's name), where the bare name is the stored value; `rebind` and `field_set` do the same for writes (`raw=True`). `construct_tuple` runs each given value through its setter after the tuple is built, never `did_set`. A lazy property's value is cached on the `TupleV` itself (`TupleV.lazy`), so `replace` makes a fresh, empty cache; `Report.title` goes through `type_member`. A `lazy` binding is a `NeedV` in the environment, forced by `ev_Name`.

Observers: `AtomV.watchers` holds `(token, property, handler)`. `swap` and `reset` call `fire_watchers` after the store, comparing the old and new value of each watched property with `values_eq`. `on_change` and `off_change` are prelude builtins; the parser turns `a.p +% h` into `on_change(a, "p", h)` and `a.p -% t` into `off_change(a, t)`, and rewrites a bare property name in `a.on_change(p, h)` into a string. The limit (`property[n]`, default 8) is enforced only without `--gc`.

Checker: `e_Field` types a property read (`prop_in`); `check_prop_write` rejects an assignment to a read-only, static, or (outside the tuple's `impl`, tracked by `impl_ty`) `priv set` property; `check_prop_reqs` compares an interface's property members with the tuple at `impl I for T`. Parse-time errors (`err_at`) cover the declaration rules: storage, setter without `field`, `did_set` on a computed property, static and lazy restrictions. `replace` and `modify` (`path_update`) write a property through its setter. Limits: observer handler types are not checked; `on_change` is typed only at run time; a setter cannot return a `Result` (a delegate's can); `layout.py` does not count a lazy property's cache slot. `rebind(env, "self", v)` writes the receiver cell of a `ref Self` method, and the checker (`method_ref`) rejects `self.n = v` in a method that isn't `ref Self`.

Result-returning setters: `parse_property` reads an optional `Result` type after `set(value: T)` (`PropertyDecl.set` is `(name, type, body, rtype)`); `expand_props` gives `__set_NAME` that return type and `_with_setter` adds the visible `set_NAME` by parsing a three-line template (`c = self`, `c.__set_NAME(value)?`, `Ok(c)`) and patching its types. `prop_set` aborts on an `Err` (a `replace`/`modify` path), and `construct_tuple` returns the `Err`, or wraps the tuple in `Ok` when any property setter or delegate `set_value` returns a `Result` (`delegate_can_fail`). The checker types such a constructor as `Result[T, Error]` (`fallible_ctor`, `delegate_fails`) and `check_prop_write` rejects plain assignment to a fallible property or delegate field. Delegates: `expand_delegates` (parser.py) finds `set_value` impls whose return type is a `Result` in the same module and adds an implicit impl after each tuple with `set_NAME` calling the builtin `__set_delegate`; `delegate_put` (places.py) is the one write path, used by `field_set` (aborts on an `Err`), `__set_delegate`, and `path_update` (so `replace` runs the delegate; it used to store the raw value). Known gap: a delegate declared in another module gets no generated `set_NAME`.

Contextual parameters (`using`), 2026-11-09: `find_using` (calls.py) now looks first in the scope of the call (`self.using_env`, set by `call_closure`), walking outward and taking the nearest scope that has a `using` value whose type fits the parameter, then in the scope where the function was defined. Before, it looked only at the definition scope, so a `using` declared in a function body was never found at a call inside that function. Two fitting values in one scope abort with "ambiguous 'using'", and a `using` parameter is itself a candidate for calls in the body. Matching is by type, never by name. The checker reports the same two errors at compile time (`check_using_args`, `check_using_param`): `Sc.usings` records each scope's `using` values and `using` parameters, a call that writes `using` must find a value of the parameter's type in an enclosing scope, and two values of exactly that type in the nearest such scope are ambiguous. It stays quiet when it can't be sure: an unknown type counts as a fit, a top-level `using` anywhere in the file counts as a possible candidate for a function body, and a call that leaves `using` out entirely (the interpreter allows it) is not checked. The run-time aborts remain as a backstop. `tests/run_using.py` covers it.

A `using` parameter must have a name: `parse_param` (pexpr.py) rejects `using Context` and `using _: Context` (an unnamed form was tried and removed, since it only saved a name and the body could not read it).

Data paths are `PathV` values, so they are first-class; `replace` and `modify` take the path at run time, so a path parameter works (the Spec allows it; a compiled implementation would specialize per path). `tests/run_paths.py` covers passing, returning, storing, composing, and updating through paths. Checker: `e_PathE` types a path as `(Root) -> Leaf` (an unknown field is a compile error); `_e_Call` hands `replace`/`modify` with three arguments to `check_path_update`, which compares the value with the root and the new value (or the function's parameter and result) with the leaf, using the argument types recorded in `arg_ty`. A path parameter is checked through its function type. Not built: the `*` traversal, positional segments, and a generic root (the parser takes NAME segments only, and the Spec now says paths take named fields only).

## The stats package (moxie/std/stats.mxi, tests/run_stats.py)

A teaching library written in moxie, found by `stdpkg.find_std` like `fp.state` (it is not in `GC_ONLY`, so it runs in both dialects). Everything takes an `Array[Double][N]`. The two-array functions `assert` equal lengths at run time, because calls into an imported package are checked from its signatures (see `import_signatures`), so the size rule below applies to `stats.covariance(a, b)`. `sort` of an array is a stream, so `sorted` collects it back into an array. The expected values in `tests/run_stats.py` were computed independently with Python's `statistics` module and numpy.

Size parameters (2026-11-09): `tys.unify` records the size of the first argument that gives a size to a parameter `N` (key `"#N"` in `binds`, kept apart from the substitution into result types) and returns a clash when another argument gives a different one, so `pair[N](a: Array[Int][N], b: Array[Int][N])` rejects arrays of different sizes. `array_size` (check.py) now also gives `x: Array[Int] = (1, 2, 3)` and `x: Array[Int] = Array(1, 2, 3)` their size, and the binding's type carries it. `tests/run_sizes.py` covers it. Not done: a `where` clause on a size (`N > 0`) is still only checked at run time.

Imported-package calls: `Checker.import_signatures(st)` (from `collect`, for each `ImportDecl`) reads the package (`package_program`: a local package, else `stdpkg.find_std`), and for every exported single-clause function adds a signature-only copy to `self.fns` as `pkg.f` (or bare `f` for `import pkg (f)`), recorded in `pkg_calls`. A parameter or result that names a type the package declares is set to untyped, and functions with higher-kinded type parameters are skipped. `pkg_redirect` (top of `_e_Call`) rewrites a copy of the call node to call that name, so the ordinary declared-function checks run (arity, argument types, generic and size unification, constant `requires`). `pipe_plan` also checks a value piped into a generic function of one parameter. `tests/run_pkgcalls.py`.
