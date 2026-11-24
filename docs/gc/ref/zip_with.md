---
layout: default
toc: true
terms: true
dialect: gc
title: "zip_with · moxie/gc function"
---

# `zip_with`

<p class="specref"><a href="../reference.html#fn-zip_with">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn zip_with[A, B, C](f (A, B) -> C, xs Seq[A], ys Seq[B]) Stream[C]
```

## Description {#description}

Walks two sources together and combines each pair of items with `f`. It is `zip` followed by `map`, in one step. It stops when the shorter source runs out.

**Parameters**

- `f`: a function of two arguments, an item from each source.
- `xs`, `ys`: the two sources.

**Returns** a `Stream[C]` of the results.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> zip_with((a, b) -> a + b, List(1, 2), List(10, 20)) |> collect()
List(11, 22)
```

