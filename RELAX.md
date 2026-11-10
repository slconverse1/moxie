# Proposals: relaxing self-imposed restrictions (2026-11-09)

Principle (Steve): a restriction that exists only for speed or safety should be the mixer's choice, not the language's. Nothing here changes syntax until approved. "Reuse" means the proposal uses existing syntax.

Status key: A = recommend, B = worth discussing, C = recommend keeping.

## 1. gc dialect: restrictions that only exist because of no-GC (A)
1. **Views can't be returned/stored/sent to `run`** (Spec: slices, views and streams). In gc a view can be an ordinary reference that keeps its parent alive. Reuse: no new syntax; `inline fn` workaround becomes optional. no-GC keeps the rule, with `copy(x)` as the escape.
2. **Concrete function-type annotations accept only no-capture functions.** In gc a closure is a heap object, so tuple fields, collection elements, and `run` arguments can hold capturing closures. no-GC keeps the rule.
3. **`any I` payload is sized for the largest type.** In gc `any` can box, so the "largest type in the program" link-time scan is unnecessary. No visible change; a simplification.
4. **Variadic spread of a `List` of unknown length** is allowed in gc with no check, since arguments need no fixed frame.

## 2. Both dialects: type-system restrictions (A/B)
5. **`any I` has no `==`, `<`, Dict key, or Set member** (A). Allow it when `I` embeds `Equatable`/`Ordered`/`Hashable`; dispatch on the tag, and values with different tags compare unequal (or order by tag). Reuse: embedding already exists.
6. **`any I` can't call `static fn` or `Self`-parameter members** (B). `Self`-parameter members (`==`, `+`) could work when both operands carry the same tag, aborting otherwise. That adds a run-time failure to a compile-time feature, so only with an explicit warning.
7. **Extension blocks (`impl Int:`) never satisfy an interface** (B). Allow a package-local retroactive impl, visible only inside that package and not exported. Reuse: `impl Describable for Int` where you don't own either side, marked `internal`. Coherence stays safe because it can't escape the package.
8. **Orphan rule** (C). Keep. Item 7 covers the real need.
9. **Interface property forms** (done): readable `name: Type` and `property` with `get`/`set` both exist. Spec section 12 was stale and is now fixed.

## 3. Functions and calls (B)
10. **Variadic spread needs a compile-time count** (B, both dialects). Allow a `List` spread with a run-time count check (abort with a clear message) plus the standard "annotate to check at compile time" warning.
11. **Return type and parameter types required on every `fn`** (C). This is a core promise; a lambda already infers.
12. **`ref` can't go to a fiber; `ref` and `lazy` don't combine** (C). Both protect ownership.
13. **Paths take named fields only** (C). Decided 2026-11-08.

## 4. Numbers and checks (B)
14. **Fixed-width overflow always aborts.** Offer per-operation choice. Reuse: `wrapping_add`, `saturating_add`, `checked_add` style functions as library functions, with no operator change. Check what the prelude already has before adding.
15. **Contracts removed in release builds** is already a choice (`keep_in_release`). No change.

## 5. Module level (B)
16. **No `global`; library files can't rebind module names.** Keep. A module-level `Atom` already covers shared state.
17. **Cycles in values** (C). Keep; immutability is the foundation of the memory model.

## Suggested order
1. Item 5 (`any` with equality and order): DONE 2026-11-09.
2. gc items 1 and 2 (views and closures), which make the two dialects differ in the direction you intended: gc lifts restrictions that exist only for no-GC.
3. Item 7 (package-local retroactive impl).
4. Items 10 and 14 after checking what exists.

Each approved item gets: Spec text in both dialects, a checker/interpreter change, tests, and a Guide sentence.

## Done 2026-11-09 (A items)
- Item 5: `any I` supports `==`, `<`, Set members, and Dict keys when `I` embeds `Equatable`/`Ordered`/`Hashable`; the checker errors otherwise; different types order by type name. Tests: tests/run_anyeq.py.
- gc items 1, 2, 4: the gc Spec already said views can be returned, closures stored anywhere, and variadics are a `List`. The reference interpreter already ran views and variadic spread; the checker still refused stored capturing closures under `--gc`, now fixed (tests/run_gcrelax.py). Item 3 (`any` boxing) has no visible effect.
