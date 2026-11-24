---
layout: default
toc: true
terms: true
dialect: gc
title: "shl · moxie/gc function"
---

# `shl`

<p class="specref"><a href="../reference.html#fn-shl">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn shl[T](a T, n Int) T
```

## Description {#description}

Shifts the bits left by `n` places, which multiplies by 2 for each place. Bits shifted out of the top are lost.

**Parameters**

- `a`: an integer.
- `n`: how many places to shift.

**Returns** an integer of the same type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> shl(1, 4)
16
```

```
> shl(cast[UInt8](255), 1)
254
```

