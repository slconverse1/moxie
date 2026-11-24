---
layout: default
toc: true
terms: true
title: "drop_while · moxie function"
---

# `drop_while`

<p class="specref"><a href="../reference.html#fn-drop_while">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn drop_while[T](f (T) -> Bool, xs Seq[T]) Stream[T]
```

## Description {#description}

Skips items from the start of a source while `f` is true, then gives the first item that fails the test and everything after it, whether or not later items pass.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a `Stream[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4, 1) |> drop_while((x) -> x < 3) |> collect()
List(3, 4, 1)
```

