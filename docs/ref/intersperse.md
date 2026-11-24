---
layout: default
toc: true
terms: true
title: "intersperse · moxie function"
---

# `intersperse`

<p class="specref"><a href="../reference.html#fn-intersperse">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn intersperse[T](sep T, xs Seq[T]) Stream[T]
```

## Description {#description}

Puts `sep` between neighbouring items. There is no separator before the first item or after the last.

**Parameters**

- `sep`: the value to put between items.
- `xs`: the items.

**Returns** a `Stream[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> intersperse(0) |> collect()
List(1, 0, 2, 0, 3)
```

