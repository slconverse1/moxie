---
layout: default
toc: true
terms: true
dialect: gc
title: "write · moxie/gc function"
---

# `write`

<p class="specref"><a href="../reference.html#fn-write">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn write[T](w ChanW[T], x T) Result[Unit, Error]
```

## Description {#description}

Puts a value into a channel. If the channel's buffer is full, the writer waits until a reader makes room.

**Parameters**

- `w`: a `ChanW[T]` (the writing end of a channel).
- `x`: the value.

**Returns** `Ok(())`, or `Err` with code `CLOSED` if the channel was closed.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> (r, w) = Chan[Int][2]()
println(write(w, 5))
Ok(())
```

