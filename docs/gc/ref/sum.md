---
layout: default
toc: true
terms: true
dialect: gc
title: "sum · moxie/gc function"
---

# `sum`

<p class="specref"><a href="../reference.html#fn-sum">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn sum[T](xs Seq[T]) T
```

## Description {#description}

Adds the items. The sum of no items is 0.

**Parameters**

- `xs`: the items, numbers of one type.

**Returns** the total, of the item type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> sum()
6
```

```
> List() |> sum()
0
```

```
> List(1.5, 2.5) |> sum()
4.0
```

