# Fix list: status

All items below are resolved in the Spec and Guide (decisions by Steve, 2026-10-26).

1. Enum case output is positional (`Maybe.Just(10)`); three Guide outputs corrected.
2. Locale format is `${x:.2n}` (type last). The interpreter still accepts `n.2f`.
3. `+` and `*` on a collection give a result sized to fit; a declared larger capacity is kept and aborts when full.
4. `Connection.open(path)` returns `Result[Connection, Error]`; `Connection.memory()` is for tests.
5. `pure` is a soft keyword (38 hard, 20 soft).
6. Guide opening notes that snippets continue from earlier ones; the gravity output is now exact.

Remaining interpreter limits (not language changes)
* sqlite has no boolean type, so BOOLEAN columns come back as `Int`; NULL becomes `()`.
* The checker's gaps, where a type error is found only at run time, are listed in Spec section 24a (the list to work down).
* Fragments not run as programs: Guide #103, #132 (deliberate error), #144 (needs a database), #140 (two files).


To do (Steve, 2026-11-09)
* Calls into an imported package are checked from its signatures, types, and functions used as values; higher-kinded parameters and nested generics are checked in the common shapes, and a delegate from another module gets `set_NAME`. Left: partly applied constructors against `M[_]`, memory spaces and pool sizing, SQL column and row types, package manifests.

* Warnings cover the gaps that remain in Spec 24a. To do: warn for any expression whose type the checker cannot work out (the stronger form; noisy until the checker leaves fewer types unknown). `--strict` / `strict = true` in `Moxie.toml` would turn the warnings into errors.

* Self-hosting: write the compiler in moxie, one piece at a time, run on the reference interpreter and tested against the Python version. Order: the lexer, then the type unifier (`tys.py`), then the parser and checker. A compiled build of the compiler is delayed until the language is final (decided by Steve, 2026-11-09). Expect to find moxie bugs this way; each goes on this list.
* Found while porting the lexer to moxie (moxie/selfhost/lexer.mxi, checked against `moxie/lexer.py` by `tests/run_selfhost.py`): (1) `join` crashed on a stream (fixed: it now drains any source); (2) a scanner loop needs its state to leave the loop: settled with no new syntax, as one state tuple that each step returns (`Lx(...st, i: st.i + 1)`) and `while cond: st = step(st)` with `else: st`, or `for ... break(k)` with `else:`; the shadow warning stays quiet when the loop's `else:` reads the name; (3) speed: appending to a list in a loop and matching operators one text slice at a time make the moxie lexer about 100 times slower than the Python one on the interpreter (900 tokens take about 25 seconds), which the compiled build is meant to fix. Not yet covered by the moxie lexer: layout tokens (INDENT/DEDENT), interpolated strings, chars, byte and raw strings, hex/suffixed numbers, block comments, `sql` blocks.

## Decisions 2026-11-10 (Steve)
- No UI kit: coders will use a native toolkit.
- Yes to a low-profile `http` socket library (std package over `Listener`/`Connection`): scope to be proposed (client, server, or both) before building.
- Superpowers: added "8. Properties" (later numbers moved up by one; cross-references updated).
