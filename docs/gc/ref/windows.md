---
layout: default
toc: true
terms: true
dialect: gc
title: "windows · moxie/gc function"
---

# `windows`

<p class="specref"><a href="../reference.html#fn-windows">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn windows[T](n Int, xs Seq[T]) Stream[List[T]]
```

## Description {#description}

Every run of `n` neighbouring items, sliding along one item at a time. A source with fewer than `n` items gives no windows.

**Parameters**

- `n`: the length of each window.
- `xs`: the items.

**Returns** a `Stream[Array[T]]`. All items are read before the first window is given.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> windows(2) |> collect()
List(List(1, 2), List(2, 3), List(3, 4))
```

```
> List(1, 2) |> windows(3) |> collect()
List()
```

