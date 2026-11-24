---
layout: default
toc: true
terms: true
dialect: gc
title: "reverse · moxie/gc function"
---

# `reverse`

<p class="specref"><a href="../reference.html#fn-reverse">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn reverse[T](xs Seq[T]) Stream[T]
```

## Description {#description}

The items in the opposite order. The whole source is read first, so it must be finite.

**Parameters**

- `xs`: the items.

**Returns** a `Stream[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> reverse() |> collect()
List(3, 2, 1)
```

