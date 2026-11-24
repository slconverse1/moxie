---
layout: default
toc: true
terms: true
title: "ok · moxie function"
---

# `ok`

<p class="specref"><a href="../reference.html#fn-ok">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn ok[T, E](r Result[T, E]) Option[T]
```

## Description {#description}

Turns a `Result` into an `Option`, keeping the value and dropping the error.

**Parameters**

- `r`: a `Result`.

**Returns** `Some(value)` for `Ok`, `None` for `Err`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> ok(Ok(1))
Some(1)
```

```
> ok(Err(Error(1, "x")))
None
```

