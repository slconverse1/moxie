---
layout: default
toc: true
terms: true
dialect: gc
title: "map_ok · moxie/gc function"
---

# `map_ok`

<p class="specref"><a href="../reference.html#fn-map_ok">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn map_ok[T, U, E](r Result[T, E], f (T) -> U) Result[U, E]
```

## Description {#description}

Applies a function to the value inside an `Ok`; an `Err` passes through untouched.

**Parameters**

- `r`: a `Result`.
- `f`: a function from the value to a new value.

**Returns** a `Result` with the new value type and the same error type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> map_ok(Ok(2), (x) -> x * 10)
Ok(20)
```

```
> map_ok(Err(Error(1, "x")), (x) -> x * 10)
Err(Error(code: 1, message: "x"))
```

