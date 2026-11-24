---
layout: default
toc: true
terms: true
title: "zip3 · moxie function"
---

# `zip3`

<p class="specref"><a href="../reference.html#fn-zip3">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn zip3[A, B, C](a Seq[A], b Seq[B], c Seq[C]) Stream[(A, B, C)]
```

## Description {#description}

Like `zip`, for three sources: it makes triples and stops when the shortest source runs out.

**Parameters**

- `a`, `b`, `c`: the three sources.

**Returns** a `Stream[(A, B, C)]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> zip3(List(1, 2), List("a", "b"), List(true, false)) |> collect()
List((1, "a", true), (2, "b", false))
```

