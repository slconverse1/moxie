---
layout: default
toc: true
terms: true
title: "or_else · moxie function"
---

# `or_else`

<p class="specref"><a href="../reference.html#fn-or_else">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn or_else[T, E, F](r Result[T, E], f (E) -> Result[T, F]) Result[T, F]
```

## Description {#description}

If the `Result` is an `Err`, try something else, which may itself fail. An `Ok` passes through untouched. It chains fallbacks: try the cache, else the disk, else the network.

**Parameters**

- `r`: a `Result`.
- `f`: a function from the error to another `Result`.

**Returns** the `Result` of the fallback, or the original `Ok`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> or_else(Err(Error(1, "x")), (e) -> Ok(0))
Ok(0)
```

```
> or_else(Ok(7), (e) -> Ok(0))
Ok(7)
```

