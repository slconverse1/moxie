---
layout: default
toc: true
terms: true
dialect: gc
title: "reject · moxie/gc function"
---

# `reject`

<p class="specref"><a href="../reference.html#fn-reject">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn reject[T](w FutureW[T], e Error) Unit
```

## Description {#description}

Completes a future with an error. Readers of the future from then on see `Future.Rejected(error)`. Like `resolve`, it uses up the writing end.

**Parameters**

- `w`: a `FutureW[T]`.
- `e`: the `Error`.

**Returns** nothing.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> (r, w) = Future[Int]()
reject(w, Error(5, "failed"))
println(read(r))
Future.Rejected(Error(code: 5, message: "failed"))
```

