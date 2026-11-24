---
layout: default
toc: true
terms: true
title: "read · moxie function"
---

# `read`

<p class="specref"><a href="../reference.html#fn-read">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn read[T](c ChanR[T]) Result[T, Error]
fn read[T](f FutureR[T]) T
```

## Description {#description}

Takes the next value from a channel, or looks at a future. Reading a channel waits, letting other fibers run, until a value is there; `Err` with code `CLOSED` means it has been closed and drained, so a loop can stop. Reading a future never waits: it tells you the state, which is `Future.Pending`, `Future.Resolved(value)` or `Future.Rejected(error)`, and it can be asked again and again with the same answer once the future is complete.

**Parameters**

- `c`: a `ChanR[T]` (the reading end of a channel), or
- `f`: a `FutureR[T]`.

**Returns** for a channel, `Result[T, Error]`; for a future, its state.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> (r, w) = Chan[Int][2]()
write(w, 5)
println(read(r))
Ok(5)
```

