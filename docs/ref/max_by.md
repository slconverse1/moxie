---
layout: default
toc: true
terms: true
title: "max_by · moxie function"
---

# `max_by`

<p class="specref"><a href="../reference.html#fn-max_by">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn max_by[T, K](f (T) -> K, xs Seq[T]) Result[T, Error]
```

## Description {#description}

The item whose key is largest. If several items have the largest key, the first of them is given.

**Parameters**

- `f`: a function from an item to its key.
- `xs`: the items.

**Returns** `Ok(item)`, or `Err` (code `MISSING`) for an empty source.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List("pear", "fig", "apple") |> max_by((s) -> len(s))
Ok("apple")
```

