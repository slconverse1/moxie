---
layout: default
toc: true
terms: true
dialect: gc
title: "split_at · moxie/gc function"
---

# `split_at`

<p class="specref"><a href="../reference.html#fn-split_at">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn split_at[T](n Int, xs Seq[T]) (List[T], List[T])
```

## Description {#description}

Splits the items after the first `n`: the first list has up to `n` items and the second has the rest.

**Parameters**

- `n`: how many items go in the first list.
- `xs`: the items.

**Returns** a pair of lists.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> split_at(1)
(List(1), List(2, 3, 4))
```

```
> List(1, 2) |> split_at(5)
(List(1, 2), List())
```

