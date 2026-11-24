---
layout: default
toc: true
terms: true
title: "scan · moxie function"
---

# `scan`

<p class="specref"><a href="../reference.html#fn-scan">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn scan[T, A](init A, f (A, T) -> A, xs Seq[T]) Stream[A]
```

## Description {#description}

Like `reduce`, but it gives every running value and not just the last. The first value given is `f(init, first item)`; `init` itself is not part of the result, so the result has one value per item.

**Parameters**

- `init`: the starting value.
- `f`: a function of the running value and the next item.
- `xs`: the items.

**Returns** a `Stream[A]` of the running values.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> scan(0, (acc, x) -> acc + x) |> collect()
List(1, 3, 6, 10)
```

