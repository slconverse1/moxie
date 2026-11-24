---
layout: default
toc: true
terms: true
dialect: gc
title: "saturating_add · moxie/gc function"
---

# `saturating_add`

<p class="specref"><a href="../reference.html#fn-saturating_add">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn saturating_add[T](a T, b T) T
```

## Description {#description}

Addition that stops at the largest or smallest value of the type instead of overflowing.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the sum, or the largest value if the true sum is too big.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> saturating_add(cast[Int8](127), cast[Int8](1))
127
```

```
> saturating_add(cast[Int8](1), cast[Int8](2))
3
```

