---
layout: default
toc: true
terms: true
title: "take_last · moxie function"
---

# `take_last`

<p class="specref"><a href="../reference.html#fn-take_last">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn take_last[T](n Int, xs Seq[T]) Stream[T]
```

## Description {#description}

The last `n` items of a source. The whole source is read before anything is given back, so it must be finite.

**Parameters**

- `n`: how many items to keep.
- `xs`: the items.

**Returns** a `Stream[T]` of at most `n` items, in their original order.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> take_last(2) |> collect()
List(3, 4)
```

