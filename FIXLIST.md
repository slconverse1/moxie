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
* Document the library code with moxie's own documentation mechanism (`moxie doc` and its doctests): `moxie/std/stats.mxi` and the `fp.*` packages should carry doc comments with runnable examples, so we practice what we preach.
* Calls into an imported package are checked from its exported signatures, its types, and its functions used as values (`Checker.import_signatures`). Left: higher-kinded type parameters and methods called on a package's type. Also open: `where` on a size that is not known at compile time is not checked at all (add a run-time abort), and a delegate declared in another module still gets no generated `set_NAME`.
