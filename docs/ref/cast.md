---
layout: default
toc: true
terms: true
title: "cast · moxie function"
---

# `cast`

<p class="specref"><a href="../reference.html#fn-cast">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn cast[T Numeric, N Numeric](x N) T
```

## Description {#description}

Converts a number to another numeric type, written with the target in brackets: `cast[Double](n)`. The conversion is explicit because moxie never widens or narrows numbers behind your back. A value that doesn't fit the target aborts (a constant that doesn't fit is a compile error); use `try_cast` to get a `Result` instead, or `wrap_to` to keep the low bits. Converting a floating-point number to an integer drops the fraction, towards zero.

**Parameters**

- `T` (in brackets): the type to convert to.
- `x`: the number.

**Returns** the value as a `T`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> cast[Double](3)
3.0
```

```
> cast[Int](2.9)
2
```

```
> cast[Int](-2.9)
-2
```

```
> cast[Int8](100)
100
```

