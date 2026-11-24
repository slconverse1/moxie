---
layout: default
toc: true
terms: true
dialect: gc
title: "bit_and · moxie/gc function"
---

# `bit_and`

<p class="specref"><a href="../reference.html#fn-bit_and">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn bit_and[T](a T, b T) T
```

## Description {#description}

Bitwise and: each bit of the result is 1 only where both inputs have a 1.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** an integer of that type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> bit_and(12, 10)
8
```

