---
layout: default
toc: true
terms: true
title: "product · moxie function"
---

# `product`

<p class="specref"><a href="../reference.html#fn-product">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn product[T](xs Seq[T]) T
```

## Description {#description}

Multiplies the items. The product of no items is 1.

**Parameters**

- `xs`: the items, numbers of one type.

**Returns** the product, of the item type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> product()
24
```

```
> List() |> product()
1
```

