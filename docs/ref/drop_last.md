---
layout: default
toc: true
terms: true
title: "drop_last · moxie function"
---

# `drop_last`

<p class="specref"><a href="../reference.html#fn-drop_last">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn drop_last[T](n Int, xs Seq[T]) Stream[T]
```

## Description {#description}

All but the last `n` items of a source. The whole source is read before anything is given back, so it must be finite.

**Parameters**

- `n`: how many items to leave out at the end.
- `xs`: the items.

**Returns** a `Stream[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> drop_last(1) |> collect()
List(1, 2, 3)
```

