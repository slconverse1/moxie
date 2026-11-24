---
layout: default
toc: true
terms: true
dialect: gc
title: "enumerate · moxie/gc function"
---

# `enumerate`

<p class="specref"><a href="../reference.html#fn-enumerate">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn enumerate[T](xs Seq[T]) Stream[(Int, T)]
```

## Description {#description}

Pairs each item with its position, counting from 0. In a `for`, a binding with two names takes each pair apart: `for i, x in xs |> enumerate()`.

**Parameters**

- `xs`: the items.

**Returns** a `Stream[(Int, T)]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List("a", "b", "c") |> enumerate() |> collect()
List((0, "a"), (1, "b"), (2, "c"))
```

