---
layout: default
toc: true
terms: true
title: "zip · moxie function"
---

# `zip`

<p class="specref"><a href="../reference.html#fn-zip">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn zip[A, B](a Seq[A], b Seq[B]) Stream[(A, B)]
```

## Description {#description}

Pairs up the items of two sources, first with first, second with second, and so on. It stops when the shorter source runs out.

**Parameters**

- `a`: the first source.
- `b`: the second source.

**Returns** a `Stream[(A, B)]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> zip(List(1, 2, 3), List("a", "b")) |> collect()
List((1, "a"), (2, "b"))
```

