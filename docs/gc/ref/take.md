---
layout: default
toc: true
terms: true
dialect: gc
title: "take · moxie/gc function"
---

# `take`

<p class="specref"><a href="../reference.html#fn-take">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn take[T](n Int, xs Seq[T]) Stream[T]
```

## Description {#description}

The first `n` items of a source. If there are fewer than `n`, all of them; if `n` is zero or negative, none. Because the stream is lazy, `take` is how you cut an endless source such as `cycle`, `repeat` or `iterate` down to a size.

**Parameters**

- `n`: how many items to keep.
- `xs`: the items.

**Returns** a `Stream[T]` of at most `n` items.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> take(2) |> collect()
List(1, 2)
```

```
> List(1, 2, 3) |> take(10) |> collect()
List(1, 2, 3)
```

```
> iterate(1, (x) -> x * 2) |> take(5) |> collect()
List(1, 2, 4, 8, 16)
```

