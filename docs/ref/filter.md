---
layout: default
toc: true
terms: true
title: "filter · moxie function"
---

# `filter`

<p class="specref"><a href="../reference.html#fn-filter">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn filter[T](f (T) -> Bool, xs Seq[T]) Stream[T]
```

## Description {#description}

Keeps the items for which `f` is true, in their original order. The result is a lazy stream.

**Parameters**

- `f`: a function from an item to a `Bool`.
- `xs`: the items.

**Returns** a `Stream[T]` of the items that passed.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4, 5) |> filter((x) -> x % 2 == 1) |> collect()
List(1, 3, 5)
```

