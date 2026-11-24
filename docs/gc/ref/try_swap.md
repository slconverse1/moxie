---
layout: default
toc: true
terms: true
dialect: gc
title: "try_swap · moxie/gc function"
---

# `try_swap`

<p class="specref"><a href="../reference.html#fn-try_swap">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn try_swap[T](a Atom[T], f (T) -> T) Result[T, Error]
```

## Description {#description}

Like `swap`, but if the atom has a validator (`Atom[T](v, valid: f)`) and the new value fails it, you get an `Err` and the atom is unchanged, where `swap` would abort.

**Parameters**

- `a`: the `Atom`.
- `f`: a function from the old value to the new one.

**Returns** `Ok(new value)`, or `Err` with code `OUT_OF_RANGE`.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> a = Atom(1)
println(try_swap(a, (x) -> x + 1))
Ok(2)
```

