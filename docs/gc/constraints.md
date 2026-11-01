---
layout: default
title: "moxie/gc: what changes"
---

# moxie/gc: what changes when the garbage collector comes back

*Draft v2. The seven decisions below were settled on 2026-10-31. Every entry under "moxie/gc" is otherwise a proposal.*

## The idea

Plain moxie has no garbage collector and no heap. That one decision explains most of its limits: capacities that are fixed up front, resources counted before the program starts, strings and temporaries that live until the next reset, closures that can't go just anywhere. moxie/gc keeps the language and replaces the memory model with a garbage-collected heap. Whatever existed only to avoid a heap goes away, and whatever expresses an idea about the language stays.

The test applied to each constraint below is simple: **would it still be needed if memory were managed for us?** If the answer is no, the constraint goes. If the answer is yes, it stays, even when it looks like a memory rule, because it really protects something else (determinism, meaning, or the one-pass compiler).

## Constraints that exist only because there's no GC

| Plain moxie | Why it exists | moxie/gc |
|---|---|---|
| Capturing closures can't be stored in a Dict, a tuple field, or a channel | A slot needs a known size, and a closure's size depends on what it captures | Closures are heap objects, so they go anywhere. Only plain functions stay special, if at all |
| A function returns one concrete closure type | Different captures mean different sizes | Any closure of the declared function type will do, so branches may return different ones |
| State monads over runtime-length data aren't possible | Same closure-size reason | They work, and `fp.state` stops being a parked item |
| Views and streams can't be returned (`inline fn` is the escape hatch) | They borrow storage that ends with the function | The collector keeps the storage alive, so they can be returned. `inline fn` is no longer needed for this |
| A value that holds a capturing closure is "transient": it can be bound, passed, and returned, but not stored | Same | The restriction disappears |
| No atoms, channels, timers, or futures created in loops or recursion | The compiler must count them before startup so the Runtime can size the pools | Create them anywhere. The pools, the compiler's tally, and the pool report are gone |
| Startup "refuses to start if it all doesn't fit" | The fixed block is sized from the tally | Gone. Running out of memory is an abort, as in most languages |
| Fiber slots are fixed (`fiber[n]`, the manifest's `[fibers] limit`), and `run` can fail with `NO_SLOT` | A block per possible fiber is allocated up front | Fibers are created on demand. `NO_SLOT` goes away, and `run` can fail only for lack of memory. A limit may stay as an optional safety cap |
| Capacities are fixed: `List`, `Dict`, `Set` declared with a size | A collection is a fixed-capacity block | `List`, `Dict`, and `Set` grow as needed. Declaring a size becomes an optional hint |
| Size parameters (`Array[T][N]`) and `where N > 0` | Sizes are compile-time types so every value has a known layout | `Array[T][N]` can stay as a way to say "exactly N" (it's also a good safety feature), but nothing requires it. Generic code over any length is just `List[T]` |
| Variadic parameters are sugar for a size parameter and are specialized per argument count | The array size is part of the type | A variadic is an ordinary list. No per-count specialization |
| S-space and T-space, with resets at loop iterations and self tail calls | Strings and temporaries would otherwise grow without bound | Gone. The collector reclaims what's dead |
| A runtime string or temporary "lasts until the next reset" and is unbound after it | Same | Every value lasts as long as it is reachable |
| A loop can't build a growing string or list by rebinding (use `reduce` or an Atom) | The reset would reclaim it | Allowed. `reduce` is still good style, but it's no longer the only way |
| `daemon:` can pass only "daemon-safe" values to its next cycle | The values have to survive the reset | A cycle can hand any value to the next one |
| `static` strings and `String[n]`, with runtime strings as a separate kind | Strings live in different places | One `String` type. Literals can still be shared |
| Recursive values (trees) have nodes in S-space and a "bounded, fixed-size form" for carrying them | Nodes need a stack to live in | Nodes are heap objects, and the bounded form is not needed |
| A runtime-built string can't be passed by `ref` | The value couldn't be written back into a binding that outlives it | Allowed |
| An `any` value is a tag plus a payload sized for the largest type converted into it, found in the link pass | No boxing | An `any` is a pointer to the value. No link-time scan is needed to size it |
| A stack, S-space, and T-space size per fiber in the manifest (`memory`, `stack`) | Fixed blocks | One heap limit, and perhaps a per-fiber stack depth |
| "Constant memory": a loop runs in bounded memory forever | Resets | Replaced by "garbage is collected." A leak is possible again, through a structure that keeps growing |
| The compiler warns when a collection exceeds a size threshold as a key | Fixed-size blocks | Likely still useful as a performance warning, but no longer a memory rule |

## Constraints that stay

These looked like memory rules, or sit nearby, but each one protects something else.

| Constraint | Why it stays |
|---|---|
| **Resources have one owner and move** (channel ends, write handles, connections, timers) | With a collector, you no longer know *when* a handle is dropped. Moxie promises that a dropped write end rejects its future with `ABANDONED`, that a channel closes when its last writer goes, and that a connection closes at a known point. Ownership and moves give those promises a deterministic time. The alternative, finalizers, is a different and weaker language |
| **No orphan impls; one hole in partial type application; no operator sections; no `_` mixed with `_1`** | Language design, not memory |
| **No import cycles; names declared before use; `forward fn`** | The one-pass compiler, which stays |
| **`ref` and `lazy` can't be combined; fibers can't receive `ref`** | Copy-in/copy-out semantics, not memory |
| **A function passed to `swap` can't park or block** | `swap` is a lock-free update, so the function has to be short and pure |
| **`any` values can't be compared** | `Self` as a parameter can't be dispatched when the type is hidden |
| **Floats can't be Dict keys** | NaN breaks equality |
| **Bounded-integer arithmetic yields plain integers** | The result can leave the range |
| **Transactions don't nest; delegates apply only to declared tuple fields** | Specification choices |
| **No structured concurrency or cancellation, for now** | Still parked |
| **One thread, cooperative fibers, no data races** | Scheduling, not memory. (A collector for a single-threaded program is also much simpler: collection can wait for a park point) |
| **Immutable values** | Always the core idea |
| **Stack overflow aborts a fiber; self tail calls reuse the frame** | The call stack is still finite |

## Decisions (settled Sat 2026-10-31)

1. **Updates use persistent structures.** `List`, `Dict`, and `Set` share structure between versions, so `list + x` and `dict + (k, v)` are cheap (O(log n) for updates and lookups). The dead-value, update-in-place analysis is dropped from the compiler. `Array[T][N]` stays flat, with O(1) indexing.
2. **A channel's size is still declared.** It says how far a writer can run ahead of its reader. An unbounded channel is a separate, explicit spelling, such as `Chan[Int][unbounded]`.
3. **Fixed-size arrays stay.** `Array[T][N]` and `MultiArray` give exact-length types. `List` is the default everywhere else.
4. **`String[n]`, `static`, and the S-space/T-space rules go away.** There is one `String` type. The Guide gets shorter.
5. **`moxie build --report` reports allocation hot spots.** It no longer reports copies and pool sizes. The details wait until the collector exists.
6. **The pitch changes.** "No GC" is replaced by "moxie without the memory limits." The Site Intro says plainly that a collector brings pauses, and says how they are kept short.
7. **One shared heap, with a generational collector that works in bounded slices at park points.** Fibers are cooperative and run one at a time, so no concurrent collector is needed. Values are immutable, so an old value never points at a newer one and no write barrier is required. Sending a value on a channel passes a pointer. The model is Go's short pauses without Go's write barrier. The Site Intro promises short pauses, not none.

## How much of the documentation would change

Plain moxie's three documents share most of their text with moxie/gc's:
- **Spec:** Section 3 (memory model), the pool and fiber-limit parts of sections 4, 18, and 19, the fixed-capacity wording in the collection and string sections, and the closure and `any` rules change. Everything about patterns, generics, interfaces, pipes, results, and fibers stays as it is.
- **Mixer's Guide:** Most chapters are identical. The chapters on collections and capacities, strings, the memory model, and daemons change, and several "Mistakes" lists get shorter.
- **Site Intro:** The superpowers are almost all the same. "No GC" is replaced by an honest account of what a collector buys, and the "Constraints from no GC" section becomes a short list of what moxie/gc *doesn't* have to worry about.

I'd write the moxie/gc documents as copies of the plain ones, with the changed passages marked so the differences are easy to find, and add a "What's different from moxie" page at the front of each.
