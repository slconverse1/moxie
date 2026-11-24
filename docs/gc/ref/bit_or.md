---
layout: default
toc: true
terms: true
dialect: gc
title: "bit_or · moxie/gc function"
---

# `bit_or`

<p class="specref"><a href="../reference.html#fn-bit_or">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn bit_or[T](a T, b T) T
```

## Description {#description}

Bitwise or: each bit of the result is 1 where either input has a 1.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** an integer of that type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> bit_or(12, 10)
14
```

