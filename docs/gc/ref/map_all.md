---
layout: default
toc: true
terms: true
dialect: gc
title: "map_all · moxie/gc function"
---

# `map_all`

<p class="specref"><a href="../reference.html#fn-map_all">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn map_all[A, B, R](f (A, B) -> R, a Result[A, Error], b Result[B, Error]) Result[R, List[Error]]
fn map_all[A, B, C, R](f (A, B, C) -> R, a Result[A, Error], b Result[B, Error], c Result[C, Error]) Result[R, List[Error]]
fn map_all[A, B, C, D, R](f (A, B, C, D) -> R, a Result[A, Error], b Result[B, Error], c Result[C, Error], d Result[D, Error]) Result[R, List[Error]]
fn map_all[A, B, C, D, E, R, E](f (A, B, C, D, E) -> R, a Result[A, E], b Result[B, E], c Result[C, E], d Result[D, E], e Result[E, E]) Result[R, List[E]]
fn map_all[A, B, C, D, E, F, R, E](f (A, B, C, D, E, F) -> R, a Result[A, E], b Result[B, E], c Result[C, E], d Result[D, E], e Result[E, E], f Result[F, E]) Result[R, List[E]]
fn map_all[A, B, R, X](rs (Result[A, X], Result[B, X]), f (A, B) -> R) Result[R, List[X]]
fn map_all[A, B, C, R, X](rs (Result[A, X], Result[B, X], Result[C, X]), f (A, B, C) -> R) Result[R, List[X]]
fn map_all[A, B, C, D, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X]), f (A, B, C, D) -> R) Result[R, List[X]]
fn map_all[A, B, C, D, E, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X], Result[E, X]), f (A, B, C, D, E) -> R) Result[R, List[X]]
fn map_all[A, B, C, D, E, F, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X], Result[E, X], Result[F, X]), f (A, B, C, D, E, F) -> R) Result[R, List[X]]
```

## Description {#description}

Combines several `Result`s with a function, and reports every error if any failed, not only the first. Give it the function and then the `Result`s (two to six of them), or a tuple of `Result`s and then the function.

**Parameters**

- `f`: a function taking the values.
- the `Result`s, separately or as a tuple.

**Returns** `Ok(f(values))` if all are `Ok`, otherwise `Err(list of every error)`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> map_all((a, b) -> a + b, Ok(1), Ok(2))
Ok(3)
```

```
> map_all((a, b) -> a + b, Err(Error(1, "x")), Err(Error(2, "y"))) |> map_err((es) -> len(es))
Err(2)
```

