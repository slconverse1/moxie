---
layout: default
toc: true
terms: true
title: "wrapping_mul · moxie function"
---

# `wrapping_mul`

<p class="specref"><a href="../reference.html#fn-wrapping_mul">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn wrapping_mul[T](a T, b T) T
```

## Description {#description}

Multiplication that wraps around on overflow.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the product modulo the size of the type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> wrapping_mul(cast[Int8](100), cast[Int8](2))
-56
```

