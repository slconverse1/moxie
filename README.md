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

**2026-11-13: Loop `else` is checked.** The Spec already said a `for` or `while` that uses `break(value)` needs an `else` of its own, but the checker accepted a loop without one (including one whose `else` was indented so it belonged to the `if`). It is now an error. The Guide points out that a loop's `else` lines up with the loop.

**2026-11-13: Chained bindings.** `x = y = z` binds `z` to `y` and then `y` to `x`, and the names may be lined up one per line with each `=` ending its line. The Guide gains a section on binding several names at once (section 1f), and "assignment" is now "binding" or "update" throughout.

**2026-11-13: Wrapped guards.** The condition of a trailing `if` may go on its own indented line under the action, for a condition too long for the line: `action` then `  if cond` means `action if cond`. A guard may also end with `else value`: if the condition fails the action is skipped and the function returns the value, like a let-else (`println("loading") if ok else fail(1, "bad")`).

**2026-11-12: Colonless syntax.** Blocks no longer start with a colon, and declarations put the type after the name (`x Int`, `fn f(x Int) Int = x * 2`). Typed bindings read the same way (`total Int = 0`). Dict entries use `key -> value`. `(:40)` is a one-item tuple, shorthand for `(0: 40)`. A bare name after a named argument is a pun for `name: name`. Colons stay in values: `User(name: "Al")`, `(x: 1, y: 2)`, `update` lines. The old syntax is on the `oldmain` branch.

## License

MIT. See `LICENSE`. It covers the interpreter and the documents.
