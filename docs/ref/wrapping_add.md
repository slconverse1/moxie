---
layout: default
toc: true
terms: true
title: "wrapping_add · moxie function"
---

# `wrapping_add`

<p class="specref"><a href="../reference.html#fn-wrapping_add">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn wrapping_add[T](a T, b T) T
```

## Description {#description}

Addition that wraps around on overflow, as a clock does: past the largest value it continues from the smallest. Without the word `wrapping`, overflow aborts. Useful for hashes and checksums.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the sum modulo the size of the type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> wrapping_add(cast[Int8](127), cast[Int8](1))
-128
```

```
> wrapping_add(cast[UInt8](250), cast[UInt8](10))
4
```

