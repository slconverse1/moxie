---
layout: default
toc: true
terms: true
title: "shr · moxie function"
---

# `shr`

<p class="specref"><a href="../reference.html#fn-shr">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn shr[T](a T, n Int) T
```

## Description {#description}

Shifts the bits right by `n` places, which divides by 2 for each place, rounding down. For a signed integer the sign is kept, so a negative number stays negative.

**Parameters**

- `a`: an integer.
- `n`: how many places to shift.

**Returns** an integer of the same type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> shr(256, 4)
16
```

```
> shr(-8, 1)
-4
```

