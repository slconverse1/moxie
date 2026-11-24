---
layout: default
toc: true
terms: true
title: "saturating_sub · moxie function"
---

# `saturating_sub`

<p class="specref"><a href="../reference.html#fn-saturating_sub">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn saturating_sub[T](a T, b T) T
```

## Description {#description}

Subtraction that stops at the largest or smallest value of the type instead of overflowing. For an unsigned type the smallest value is 0.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the difference, limited to what the type can hold.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> saturating_sub(cast[UInt8](1), cast[UInt8](5))
0
```

```
> saturating_sub(cast[Int8](-100), cast[Int8](100))
-128
```

