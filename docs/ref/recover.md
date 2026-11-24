---
layout: default
toc: true
terms: true
title: "recover · moxie function"
---

# `recover`

<p class="specref"><a href="../reference.html#fn-recover">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn recover[T, E](r Result[T, E], f (E) -> T) Result[T, E]
```

## Description {#description}

If the `Result` is an `Err`, replace it with a plain value from a function; the result is then always an `Ok`.

**Parameters**

- `r`: a `Result`.
- `f`: a function from the error to a value.

**Returns** an `Ok`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> recover(Err(Error(1, "x")), (e) -> 0)
Ok(0)
```

```
> recover(Ok(5), (e) -> 0)
Ok(5)
```

