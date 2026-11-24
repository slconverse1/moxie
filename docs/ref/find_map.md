---
layout: default
toc: true
terms: true
title: "find_map · moxie function"
---

# `find_map`

<p class="specref"><a href="../reference.html#fn-find_map">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn find_map[T, U](f (T) -> Option[U], xs Seq[T]) Result[U, Error]
```

## Description {#description}

Applies `f`, which gives an `Option`, to the items in turn and returns the first value that is present, without looking at the rest.

**Parameters**

- `f`: a function from an item to an `Option`.
- `xs`: the items.

**Returns** `Ok(value)` for the first `Some`, or `Err` (code `MISSING`) if every result is `None`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> find_map((x) -> if x > 1 then Some(x * 10) else None)
Ok(20)
```

