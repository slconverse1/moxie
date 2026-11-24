---
layout: default
toc: true
terms: true
dialect: gc
title: "frequencies · moxie/gc function"
---

# `frequencies`

<p class="specref"><a href="../reference.html#fn-frequencies">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn frequencies[T](xs Seq[T]) Dict[T, Int]
```

## Description {#description}

Counts how many times each item occurs.

**Parameters**

- `xs`: the items.

**Returns** a `Dict[T, Int]` from item to count, in the order each item was first seen.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 1, 3, 1) |> frequencies()
Dict(1 -> 3, 2 -> 1, 3 -> 1)
```

