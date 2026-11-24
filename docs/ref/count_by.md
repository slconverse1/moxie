---
layout: default
toc: true
terms: true
title: "count_by · moxie function"
---

# `count_by`

<p class="specref"><a href="../reference.html#fn-count_by">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn count_by[T, K](f (T) -> K, xs Seq[T]) Dict[K, Int]
```

## Description {#description}

Counts how many items have each key.

**Parameters**

- `f`: a function from an item to its key.
- `xs`: the items.

**Returns** a `Dict[K, Int]` from key to count.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4, 5) |> count_by((x) -> x % 2)
Dict(1 -> 3, 0 -> 2)
```

