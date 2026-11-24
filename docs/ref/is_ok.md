---
layout: default
toc: true
terms: true
title: "is_ok · moxie function"
---

# `is_ok`

<p class="specref"><a href="../reference.html#fn-is_ok">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn is_ok[T, E](r Result[T, E]) Bool
```

## Description {#description}

True if a `Result` is `Ok`.

**Parameters**

- `r`: a `Result`.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> is_ok(Ok(1))
true
```

```
> is_ok(Err(Error(1, "x")))
false
```

