---
layout: default
toc: true
terms: true
dialect: gc
title: "drop · moxie/gc function"
---

# `drop`

<p class="specref"><a href="../reference.html#fn-drop">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn drop[T](n Int, xs Seq[T]) Stream[T]
```

## Description {#description}

All but the first `n` items. If there are `n` or fewer items, the result is empty; if `n` is zero or negative, nothing is dropped.

**Parameters**

- `n`: how many items to skip.
- `xs`: the items.

**Returns** a `Stream[T]` of the rest.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> drop(2) |> collect()
List(3, 4)
```

```
> List(1, 2, 3) |> drop(5) |> collect()
List()
```

