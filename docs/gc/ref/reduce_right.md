---
layout: default
toc: true
terms: true
dialect: gc
title: "reduce_right · moxie/gc function"
---

# `reduce_right`

<p class="specref"><a href="../reference.html#fn-reduce_right">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn reduce_right[T, A](init A, f (T, A) -> A, xs Seq[T]) A
```

## Description {#description}

Like `reduce`, but it works from the end of the source towards the start, and `f` takes the item first and the running value second: `f(item, acc)`.

**Parameters**

- `init`: the starting value.
- `f`: a function of an item and the running value.
- `xs`: the items; read in full before folding, so it must be finite.

**Returns** the final value.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> reduce_right(0, (x, acc) -> x - acc)
2
```

