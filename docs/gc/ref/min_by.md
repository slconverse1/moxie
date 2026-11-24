---
layout: default
toc: true
terms: true
dialect: gc
title: "min_by · moxie/gc function"
---

# `min_by`

<p class="specref"><a href="../reference.html#fn-min_by">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn min_by[T, K](f (T) -> K, xs Seq[T]) Result[T, Error]
```

## Description {#description}

The item whose key is smallest. If several items have the smallest key, the first of them is given.

**Parameters**

- `f`: a function from an item to its key.
- `xs`: the items.

**Returns** `Ok(item)`, or `Err` (code `MISSING`) for an empty source.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List("pear", "fig", "apple") |> min_by((s) -> len(s))
Ok("fig")
```

