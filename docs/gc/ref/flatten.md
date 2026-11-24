---
layout: default
toc: true
terms: true
dialect: gc
title: "flatten · moxie/gc function"
---

# `flatten`

<p class="specref"><a href="../reference.html#fn-flatten">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn flatten[T](xs Seq[Seq[T]]) Stream[T]
```

## Description {#description}

Turns a source of sources into one source, taking the inner items in order. Each inner item may be a list, an array or another stream.

**Parameters**

- `xs`: a source whose items are themselves sources.

**Returns** a `Stream[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(List(1, 2), List(), List(3)) |> flatten() |> collect()
List(1, 2, 3)
```

