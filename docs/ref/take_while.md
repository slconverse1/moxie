---
layout: default
toc: true
terms: true
title: "take_while · moxie function"
---

# `take_while`

<p class="specref"><a href="../reference.html#fn-take_while">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn take_while[T](f (T) -> Bool, xs Seq[T]) Stream[T]
```

## Description {#description}

Items from the start of a source for as long as `f` is true. It stops at the first item for which `f` is false, even if later items would pass.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a `Stream[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4, 1) |> take_while((x) -> x < 3) |> collect()
List(1, 2)
```

