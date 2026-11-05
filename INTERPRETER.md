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
A mixer-written `Generatable` is found through `I.statics[T]["generate"]` and `I.impls[T]["shrink"]`
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
`sys.platform` is `emscripten`. The interpreter has not been run under real Pyodide in this
environment (no network to fetch it): the worker's Python was run under CPython. Tests:
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
`to_local` is in `effects.SYSTEM_CALLS`. Zone names need a time zone database on the host (the Python
`zoneinfo` module reads the system's, or the `tzdata` package); where there is none the zone
functions return `NOT_FOUND`. Not yet checked under Pyodide. Tests: `tests/run_datetime.py`.
