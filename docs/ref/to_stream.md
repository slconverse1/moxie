---
layout: default
toc: true
terms: true
title: "to_stream · moxie function"
---

# `to_stream`

<p class="specref"><a href="../reference.html#fn-to_stream">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn to_stream[T](xs Seq[T]) Stream[T]
```

## Description {#description}

Treats any collection as a stream, so that stream functions can be applied to it with `|>`. A `Stream` given to it comes back unchanged.

**Parameters**

- `xs`: a `List`, `Array`, `Set`, `Ring` or `Stream`.

**Returns** a `Stream[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(7, 8) |> to_stream() |> collect()
List(7, 8)
```

