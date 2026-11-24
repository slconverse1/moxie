---
layout: default
toc: true
terms: true
title: "sort · moxie function"
---

# `sort`

<p class="specref"><a href="../reference.html#fn-sort">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn sort[T Ordered](xs Seq[T]) Stream[T]
```

## Description {#description}

Orders the items from smallest to largest by `<`. The sort is stable: items that compare equal keep their original order. The items must be orderable: numbers, text and characters are, and a tuple or enum you declare is when it says `deriving ord` (or has an `impl Ordered`). The whole source is read first, so it must be finite.

**Parameters**

- `xs`: the items.

**Returns** a `Stream[T]` in order. Use `sort_by` to order by a key instead of the item itself.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(3, 1, 2) |> sort() |> collect()
List(1, 2, 3)
```

```
> List("pear", "apple", "fig") |> sort() |> collect()
List("apple", "fig", "pear")
```

