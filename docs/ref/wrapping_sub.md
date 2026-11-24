---
layout: default
toc: true
terms: true
title: "wrapping_sub · moxie function"
---

# `wrapping_sub`

<p class="specref"><a href="../reference.html#fn-wrapping_sub">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn wrapping_sub[T](a T, b T) T
```

## Description {#description}

Subtraction that wraps around on overflow.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the difference modulo the size of the type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> wrapping_sub(cast[UInt8](0), cast[UInt8](1))
255
```

