# Draft: dropping provably redundant bounds checks (design note, NOT in the Spec; nothing implemented)

Status: for a future compiler backend. The reference interpreter always checks, so it gains nothing. The examples below are
illustrations and have not been run.

## Rule (proposed Spec text)

A compiler may omit a run-time check only when the checker has proved it can never fail. The checked and unchecked programs
then behave identically, so this is an optimization, not a feature, and needs no `unsafe` construct. A check the compiler
cannot prove stays. Out-of-range `a(i)` still aborts; `get(a, i)` still returns `Result`.

## Cases the checker proves (the whole list for now)

1. A bounded index into a sized collection whose range fits:
   ```
   a: Array[Int][8] = ...
   i: Int[0..=7] = ...
   a(i)
   ```
2. A loop variable over the collection's own length, since values are immutable and the length cannot change under the name:
   ```
   for i in 0..len(a):
     a(i)
   ```
3. A function whose `requires` states the bound (`requires i < len(a)`), inside its body.

Iteration (`for x in a`) has no index and nothing to check.

## Not proposed

- Bounds that depend on other values (`Int[0..n]`), which the Spec rules out today. General cases would need dependent types
  or a theorem prover; the three cases above cover most loops.
- A general `unsafe` package. FFI (Spec 19a, the `ffi` permission) stays the one place where safety ends.

## Safeguards

- **Debug builds and `moxie test` keep every check**, including the ones a release build drops, and treat a failure of a
  "proved" check as a compiler bug. A wrong proof then fails a test instead of corrupting memory.
- **Report mode (opt in):** `moxie build --explain-checks` lists the checks dropped and the ones kept, with the reason, so a
  mixer tuning a hot loop can see what to change. The default build stays quiet; no warning on an unprovable index.

## Open questions

- Is the proof only inside one function, or across calls (a `Int[0..=7]` parameter passed along)? Start inside one function.
- `len` on a `String` counts bytes, so case 2 applies to sequences only, not to strings.
