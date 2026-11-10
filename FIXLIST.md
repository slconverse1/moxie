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
- Yes to a low-profile `http` socket library: built 2026-11-10 as `moxie/std/http.mxi` (client get/post/request, server serve_one/serve_n/serve; text bodies, Connection: close). Added `to_utf8`/`from_utf8` for it. Not yet: TLS (`connect_tls` exists in the prelude, so an `https` client is a small step), chunked bodies, keep-alive, binary bodies, the browser platform, and a `\r` string escape (the package builds CRLF from bytes).
- Superpowers: added "8. Properties" (later numbers moved up by one; cross-references updated).

- Site look to keep (2026-11-10): the dialect note on each intro is a Markdown quote that the layout draws as a green-bordered box, with blue links in the page content. Saved as the GitHub branch `saved/site-intro-box-2026-11-10` (a tag could not be pushed); restore with `git checkout origin/saved/site-intro-box-2026-11-10 -- docs/_layouts/default.html docs/index.md docs/gc/index.md`.

## Self-hosted lexer progress (2026-11-10)
- Done and compared with `moxie/lexer.py` (884 tokens over 77 lines of std and examples agree): names, plain ints and decimals, plain strings, operators, `//` comments, and the logical-line pass (NL, INDENT, DEDENT, EOF, continuation lines by open brackets, dangling operators, leading `|>` and `.name`, `requires`/`ensures` and property accessors).
- Found: a rebinding inside a nested `if` in a loop body does not carry to the next iteration (the first lexer loop hung, and so did the first `group_lines`); use a state tuple and a step function. A field followed by `(...)` reads as a method call (`g.cur(n)`), so index through a helper function. `list + list` concatenates, so add a row to a list of lists as `rows + List(row)`.
- Still to do: interpolated strings, chars, hex/underscore/suffixed numbers, byte and raw strings, `/* */` comments, `sql` blocks, tab errors and the error cases ("unexpected indent" is an `ERR` token for now).

- Fixed 2026-11-10: a fiber abort while another fiber waited on a socket read left the process hanging (closing the socket blocked on the reader's lock); sockets are now shut down before they are closed. Test: tests/run_http.py.

- Orphan impls (2026-11-10, Steve's decision): a package may impl a foreign interface for a foreign type (no wrapper tuple). Such an impl is private to the package and importers never see it (checker skips it when registering imported methods). Spec 12 updated in both dialects. NOT yet enforced: the clash error when the interface already has a visible impl for the type; no test yet for a private local impl.
- Local impls, follow-up (2026-11-10): the clash check is built (a second impl of the same interface for the same qualified type in a file is an error, and so is one that repeats an impl an imported package gives its own type; generic impls are skipped). Test in run_packages.py. KNOWN GAP: the interpreter keeps one global method table, so an importer can still call another package's private impl at run time (`mid.mk().say()` ran), and the checker doesn't flag it. Fix needs package-scoped method tables. Clash with impls of built-in types (Int, etc.) is not covered either.
