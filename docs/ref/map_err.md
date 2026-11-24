---
layout: default
toc: true
terms: true
title: "map_err · moxie function"
---

# `map_err`

<p class="specref"><a href="../reference.html#fn-map_err">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn map_err[T, E, F](r Result[T, E], f (E) -> F) Result[T, F]
```

## Description {#description}

Applies a function to the error inside an `Err`, for example to wrap it in your own error type; an `Ok` passes through untouched.

**Parameters**

- `r`: a `Result`.
- `f`: a function from the old error to the new one.

**Returns** a `Result` with the same value type and the new error type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> map_err(Err(Error(1, "x")), (e) -> e.code)
Err(1)
```

```
> map_err(Ok(1), (e) -> 0)
Ok(1)
```

