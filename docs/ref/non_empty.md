---
layout: default
toc: true
terms: true
title: "non_empty · moxie function"
---

# `non_empty`

<p class="specref"><a href="../reference.html#fn-non_empty">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn non_empty[T](xs List[T]) Result[NonEmpty[T], Error]
```

## Description {#description}

Checks that an `Option` or list has something in it, as a `Result`.

**Parameters**

- `x`: an `Option` or a `List`.

**Returns** for a list, `Ok` of a `NonEmpty` (a `head` and a `tail`, so the first item is always there); for an `Option`, `Ok(value)`. Otherwise an `Err` with code `MISSING`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> non_empty(List(1))
Ok(NonEmpty(head: 1, tail: List()))
```

```
> non_empty(List())
Err(Error(code: 4, message: "empty"))
```

