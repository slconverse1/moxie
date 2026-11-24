---
layout: default
toc: true
terms: true
dialect: gc
title: "bit_xor · moxie/gc function"
---

# `bit_xor`

<p class="specref"><a href="../reference.html#fn-bit_xor">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn bit_xor[T](a T, b T) T
```

## Description {#description}

Bitwise exclusive or: each bit of the result is 1 where the inputs differ.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** an integer of that type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> bit_xor(12, 10)
6
```

