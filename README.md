# moxie

Moxie is a language-design exercise: (mostly) compile-time type-safe, immutable, practical functional programming, Go-style channels and fibers, and, in the plain dialect, no garbage collector and no heap. A second dialect, moxie/gc, adds a collector; the two are kept apart because they make different promises. This repository holds the language documents and a reference interpreter written in plain Python 3.

- **Site:** https://slconverse1.github.io/moxie/ (the Site Intro, Tutorial, Mixer's Guide, Spec, and an in-browser "Try moxie" page)
- **`docs/`** the documents, as the site's source: `index.md` (Site Intro), `tutorial.md`, `guide.md`, `spec.md`, and `gc/` for moxie/gc, the garbage-collected dialect (its Site Intro, Spec, and Guide)
- **`moxie/`** the reference interpreter (standard library only)
- **`examples/`**, **`tests/`**, **`INTERPRETER.md`**, **`FIXLIST.md`** the interpreter's samples, tests, notes, and a list of problems found in the Spec and Guide

## Run a program

    git clone https://github.com/slconverse1/moxie
    cd moxie
    python3 -m moxie run examples/gradebook.mxi
    python3 -m moxie test examples/gradebook.mxi

The interpreter needs Python 3.11 or later (tested on 3.11, 3.12, and 3.13) and nothing else. `INTERPRETER.md` lists what it checks and what it doesn't yet.

## Changes

Newest first.

**2026-11-14: one code for "not there".** `get(xs, i)` on a List or Array and `Enum.from_index(n)` now give `MISSING` (4), as a Dict key, `first` of nothing and `value_of` already did; they used to give `OUT_OF_RANGE` (6). The rule is in Spec section 6 (the `Error` entry): `MISSING` is an element, key or case the program's own data lacks, `NOT_FOUND` is a thing outside it (file, host, zone), `OUT_OF_RANGE` is a number outside its allowed range. A program that matched `OUT_OF_RANGE` on a failed `get` of a List needs `MISSING`. `tests/run_notfound.py`.

**2026-11-14: constant indexes into Lists.** `xs = List(1, 2, 3)` then `xs(3)` is a compile error (as it already was for an Array), and so is a negative constant index into any List or Array. A List counts only when its name is bound once and never changed through `ref`, a `ref` method or `+=`, so the length is the text's. `xs(i)` stays the element itself and aborts on a bad index; `get(xs, i)` is the version that returns a `Result`. `tests/run_indexcheck.py`.

**2026-11-14: let-else can see the failure.** `Ok(n) = read[Int](t) else Err(e) -> Err(wrap(e))`: the else takes a pattern of its own, so the `Err`'s code and message are in scope (to log, to convert). The two patterns must cover every case together, as in `when`, and the old `else value` form is unchanged. Guide chapter 12, Spec section 1, `tests/run_letelse.py`.

**2026-11-14: `dynamic fn`, `unsafe fn`, `deriving dyn`.** Reading a `Dyn` (`field`, `at`, `as_*`, `from_dyn`) now has to happen in a function marked `dynamic fn`, and calling a foreign function marked `unsafe` (or taking a `Ptr[T]`) in one marked `unsafe fn`; unmarked use is a compile error, top-level script code is exempt, and `dynamic`/`unsafe` stay usable as variable names. Only the function that does the thing is marked, so a checking wrapper can be called from anywhere; `safety = "strict"` under `[program]` in `Moxie.toml` makes callers carry the mark too. `deriving dyn` on a tuple writes `to_dyn()` and a checked `Tuple.from_dyn(d)` (a `Result`, naming the missing key or wrong kind) at compile time from the field types: `Int`, `Float`, `Bool`, `String`, `List` of those, and nested tuples that derive it. Guide chapter on JSON, Spec 23c/23d, `tests/run_safety.py`.

**2026-11-14: `proxy`.** `impl Printer for Logger proxy(printer)` hands a whole interface to a field: the methods the block doesn't write forward to the field, so only the ones that differ are written (Kotlin's class delegation). Guide chapter 9a. Plain methods of an interface declared in the same file only; `static`, `ref`, generic and `Self` members are errors that say to write them by hand.

**2026-11-14: Three more mistakes caught at compile time.** A pattern that can never match its value (`Some(n)` against a `Result`) is an error, in `when`, `is` and let-else. Dropping a `Result` as a statement is a warning (write `\ call()` to drop it on purpose). `cast[UInt8](300)` of a constant that does not fit is an error.

**2026-11-13: Union elements and `elif` chains.** The loop variable over a list of a union is a union (`for x in ids`, then `x + 1` is an error until tested), and so is `ids(i)`; `if ids(0) is Int` narrows that element. An `if`/`elif` chain in which some arms leave now narrows what follows, from the arms that stay.

**2026-11-13: Narrowing after an early exit, and with `not` and `or`.** `if not (v is Int) then return 0` now makes `v` an `Int` on the following lines; `break`, `continue` and the guard forms work the same, as do field paths. `not` and `or` narrow, and a test that leaves several members leaves a union of those. A branch that doesn't leave narrows nothing after it. `==` never narrows.

**2026-11-13: Union values are checked.** A value of a `type union` is one of its members, so using it as one (`v + 1`, `len(v)`) is now a compile error until `is` or a `when` says which. `if v is T` narrows the then-branch, each `elif`, the `else` when one member is left, the right side of `and`, and field paths (`p.f`). `println`, interpolation, `==` and passing the union on need no test. Before this the checker let any use of a union through.

**2026-11-13: Bare tuples.** A function can end with `a, b` (or `return a, b`) instead of `(a, b)`, matching `lo, hi = f()`.

**2026-11-13: `json` package and `Dyn`.** `import json` gives a closed `Dyn` enum with `json.parse(text)`, `d.field(key)`, `d.at(i)`, `as_int()` and friends (all `Result`), and `to_json()`. It is written in moxie, uses no reflection, and works in both dialects. Conversion to and from your own types (`deriving dyn`) and the `dynamic fn` marker are not built yet (FIXLIST).

**2026-11-13: Chained comparisons.** `0 <= x <= 100` means `0 <= x and x <= 100`. Any run of `<`, `<=`, `>`, `>=` and `==` chains (`a == b == c` means all equal); a middle operand is evaluated once and the chain stops at the first false link. `~=` does not chain (an error says to use `and`). `(a < b) == flag` now needs its parentheses.

**2026-11-13: Loop `else` is checked.** The Spec already said a `for` or `while` that uses `break(value)` needs an `else` of its own, but the checker accepted a loop without one (including one whose `else` was indented so it belonged to the `if`). It is now an error. The Guide points out that a loop's `else` lines up with the loop.

**2026-11-13: Chained bindings.** `x = y = z` binds `z` to `y` and then `y` to `x`, and the names may be lined up one per line with each `=` ending its line. The Guide gains a section on binding several names at once (section 1f), and "assignment" is now "binding" or "update" throughout.

**2026-11-13: Wrapped guards.** The condition of a trailing `if` may go on its own indented line under the action, for a condition too long for the line: `action` then `  if cond` means `action if cond`. A guard may also end with `else value`: if the condition fails the action is skipped and the function returns the value, like a let-else (`println("loading") if ok else fail(1, "bad")`).

**2026-11-12: Colonless syntax.** Blocks no longer start with a colon, and declarations put the type after the name (`x Int`, `fn f(x Int) Int = x * 2`). Typed bindings read the same way (`total Int = 0`). Dict entries use `key -> value`. `(:40)` is a one-item tuple, shorthand for `(0: 40)`. A bare name after a named argument is a pun for `name: name`. Colons stay in values: `User(name: "Al")`, `(x: 1, y: 2)`, `update` lines. The old syntax is on the `oldmain` branch.

## License

MIT. See `LICENSE`. It covers the interpreter and the documents.
