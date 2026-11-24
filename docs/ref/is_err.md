---
layout: default
toc: true
terms: true
title: "is_err · moxie function"
---

# `is_err`

<p class="specref"><a href="../reference.html#fn-is_err">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn is_err[T, E](r Result[T, E]) Bool
```

## Description {#description}

True if a `Result` is `Err`.

**Parameters**

- `r`: a `Result`.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> is_err(Ok(1))
false
```

```
> is_err(Err(Error(1, "x")))
true
```

