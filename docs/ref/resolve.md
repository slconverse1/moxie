---
layout: default
toc: true
terms: true
title: "resolve · moxie function"
---

# `resolve`

<p class="specref"><a href="../reference.html#fn-resolve">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn resolve[T](w FutureW[T], v T) Unit
```

## Description {#description}

Completes a future with a value. Everyone who reads the future from then on sees `Future.Resolved(value)`. A future is completed only once, and `resolve` uses up the writing end, so a second call is a compile error.

**Parameters**

- `w`: a `FutureW[T]`.
- `v`: the value.

**Returns** nothing.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> (r, w) = Future[Int]()
resolve(w, 5)
println(read(r))
Future.Resolved(5)
```

