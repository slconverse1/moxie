---
layout: default
toc: true
terms: true
dialect: gc
title: "filter_map · moxie/gc function"
---

# `filter_map`

<p class="specref"><a href="../reference.html#fn-filter_map">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn filter_map[T, U](f (T) -> Option[U], xs Seq[T]) Stream[U]
```

## Description {#description}

Applies `f`, which gives an `Option`, to every item and keeps the values from the `Some` results. It does a `map` and a `filter` in one step.

**Parameters**

- `f`: a function from an item to an `Option`; `None` drops the item.
- `xs`: the items.

**Returns** a `Stream[U]` of the values that were present.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> filter_map((x) -> if x > 1 then Some(x * 10) else None) |> collect()
List(20, 30)
```

