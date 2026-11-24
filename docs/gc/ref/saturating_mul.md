---
layout: default
toc: true
terms: true
dialect: gc
title: "saturating_mul · moxie/gc function"
---

# `saturating_mul`

<p class="specref"><a href="../reference.html#fn-saturating_mul">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn saturating_mul[T](a T, b T) T
```

## Description {#description}

Multiplication that stops at the largest or smallest value of the type instead of overflowing.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the product, limited to what the type can hold.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> saturating_mul(cast[Int8](100), cast[Int8](2))
127
```

