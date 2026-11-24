---
layout: default
toc: true
terms: true
title: "sort_by · moxie function"
---

# `sort_by`

<p class="specref"><a href="../reference.html#fn-sort_by">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn sort_by[T, K](f (T) -> K, xs Seq[T]) Stream[T]
```

## Description {#description}

Orders the items by a key that `f` computes from each one, smallest key first. The sort is stable, so items with equal keys keep their original order. The whole source is read first, so it must be finite.

**Parameters**

- `f`: a function from an item to its sort key.
- `xs`: the items.

**Returns** a `Stream[T]` in key order.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List("pear", "fig", "apple") |> sort_by((s) -> len(s)) |> collect()
List("fig", "pear", "apple")
```

