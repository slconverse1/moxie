---
layout: default
toc: true
terms: true
title: "chunks · moxie function"
---

# `chunks`

<p class="specref"><a href="../reference.html#fn-chunks">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn chunks[T](n Int, xs Seq[T]) Stream[List[T]]
```

## Description {#description}

Groups the items in lists of `n`, in order. The last list is shorter when the number of items is not a multiple of `n`.

**Parameters**

- `n`: the size of each group.
- `xs`: the items.

**Returns** a `Stream[List[T]]`. All items are read before the first group is given.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4, 5) |> chunks(2) |> collect()
List(List(1, 2), List(3, 4), List(5))
```

