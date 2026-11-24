---
layout: default
toc: true
terms: true
dialect: gc
title: "par_map · moxie/gc function"
---

# `par_map`

<p class="specref"><a href="../reference.html#fn-par_map">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn par_map[T, U](f (T) -> U, xs Seq[T], limit: Int) List[U]
```

## Description {#description}

Applies a function to every item, running up to `limit` calls at the same time, and returns the results in the original order, whatever order they finished in. The `limit` must be a constant number, because in moxie the fibers are counted before the program runs.

**Parameters**

- `f`: a function from an item to a result.
- `xs`: the items.
- `limit:`: how many calls may run at once.

**Returns** a `List` of results, in the order of `xs`.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> par_map((x) -> x * x, List(1, 2, 3, 4), limit: 2)
List(1, 4, 9, 16)
```

