---
layout: default
toc: true
terms: true
dialect: gc
title: "clamp · moxie/gc function"
---

# `clamp`

<p class="specref"><a href="../reference.html#fn-clamp">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn clamp[T](x T, lo T, hi T) T
fn clamp[T](x T, r Range) T
```

## Description {#description}

Limits a value to a range: below the low bound it gives the low bound, above the high bound it gives the high bound, and otherwise the value itself.

**Parameters**

- `x`: the value.
- `lo`, `hi`: the bounds; or
- `r`: a range such as `0..10`.

**Returns** a value of the same type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> clamp(15, 0, 10)
10
```

```
> clamp(5, 0, 10)
5
```

```
> clamp(-5, 0, 10)
0
```

```
> clamp(2.5, 0.0, 1.0)
1.0
```

```
> clamp(15, 0..10)
10
```

