---
layout: default
toc: true
terms: true
dialect: gc
title: "bit_not · moxie/gc function"
---

# `bit_not`

<p class="specref"><a href="../reference.html#fn-bit_not">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn bit_not[T](a T) T
```

## Description {#description}

Bitwise complement: every 0 bit becomes 1 and every 1 bit becomes 0. For a signed integer, `bit_not(n)` is `-n - 1`.

**Parameters**

- `a`: an integer.

**Returns** an integer of the same type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> bit_not(0)
-1
```

```
> bit_not(5)
-6
```

