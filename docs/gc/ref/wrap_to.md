---
layout: default
toc: true
terms: true
dialect: gc
title: "wrap_to · moxie/gc function"
---

# `wrap_to`

<p class="specref"><a href="../reference.html#fn-wrap_to">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn wrap_to[T Numeric, N Numeric](x N) T
```

## Description {#description}

Converts an integer to a narrower or differently signed type by keeping the low bits, as a C cast would. Nothing aborts; values that don't fit wrap around.

**Parameters**

- `T` (in brackets): the type to convert to.
- `x`: the integer.

**Returns** the value as a `T`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> wrap_to[Int8](300)
44
```

```
> wrap_to[UInt8](-1)
255
```

