---
layout: default
toc: true
terms: true
dialect: gc
title: "transpose · moxie/gc function"
---

# `transpose`

<p class="specref"><a href="../reference.html#fn-transpose">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn transpose[T](rows Seq[Seq[T]]) List[List[T]]
```

## Description {#description}

Turns rows into columns: the first list gets the first item of every row, the second list the second item, and so on. Rows of different lengths are allowed; a short row just has nothing in the later columns.

**Parameters**

- `rows`: a source of rows, each a source of items.

**Returns** a `List[List[T]]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> transpose(List(List(1, 2, 3), List(4, 5)))
List(List(1, 4), List(2, 5), List(3))
```

