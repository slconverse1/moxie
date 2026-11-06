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
* Static checks are conservative: generics are checked only in part (see the Spec) and unions are unchecked; implicit Int to Double for non-literals is not flagged.
* Fragments not run as programs: Guide #103, #132 (deliberate error), #144 (needs a database), #140 (two files).
* Generic types are not checked (see TYPE-LEVEL.md): `b: Box[Int] = Box(v: "x")`, `x: Array[Int][3] = Array(1, 2)`, and a `String` returned into an `Int` from `first(Array("a", "b", "c"))` all pass `moxie check`. The checker has no representation for parameterized types.
