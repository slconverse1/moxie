---
layout: default
toc: true
terms: true
dialect: gc
title: "distinct · moxie/gc function"
---

# `distinct`

<p class="specref"><a href="../reference.html#fn-distinct">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn distinct[T Equatable](xs Seq[T]) Stream[T]
```

## Description {#description}

Drops repeated items, keeping the first of each, in their original order. Items must have `==` (`deriving eq` for a tuple or enum you declare).

**Parameters**

- `xs`: the items.

**Returns** a `Stream[T]` with no repeats.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 1, 2, 1, 3, 2) |> distinct() |> collect()
List(1, 2, 3)
```

