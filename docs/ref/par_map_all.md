---
layout: default
toc: true
terms: true
title: "par_map_all · moxie function"
---

# `par_map_all`

<p class="specref"><a href="../reference.html#fn-par_map_all">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn par_map_all[A, B, R, X](f (A, B) -> R, c1 () -> Result[A, X], c2 () -> Result[B, X]) Result[R, List[X]]
fn par_map_all[A, B, C, R, X](f (A, B, C) -> R, c1 () -> Result[A, X], c2 () -> Result[B, X], c3 () -> Result[C, X]) Result[R, List[X]]
fn par_map_all[A, B, C, D, R, X](f (A, B, C, D) -> R, c1 () -> Result[A, X], c2 () -> Result[B, X], c3 () -> Result[C, X], c4 () -> Result[D, X]) Result[R, List[X]]
fn par_map_all[A, B, C, D, E, R, X](f (A, B, C, D, E) -> R, c1 () -> Result[A, X], c2 () -> Result[B, X], c3 () -> Result[C, X], c4 () -> Result[D, X], c5 () -> Result[E, X]) Result[R, List[X]]
fn par_map_all[A, B, C, D, E, F, R, X](f (A, B, C, D, E, F) -> R, c1 () -> Result[A, X], c2 () -> Result[B, X], c3 () -> Result[C, X], c4 () -> Result[D, X], c5 () -> Result[E, X], c6 () -> Result[F, X]) Result[R, List[X]]
```

## Description {#description}

Like `map_all`, but each input is a function that is run in its own fiber, so they run at the same time, and every error is collected. Give it the combining function and then two to six functions that each make a `Result`.

**Parameters**

- `f`: a function taking the values.
- `c1`, `c2`, ...: functions that take no arguments and return a `Result`.
- `limit:`: how many fibers may run at once, a constant of 1 or more.

**Returns** `Ok(f(values))` if all succeed, otherwise `Err(list of every error)`.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> par_map_all((a, b) -> a + b, () -> Ok(1), () -> Ok(2), limit: 2)
Ok(3)
```

