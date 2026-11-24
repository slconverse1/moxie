---
layout: default
toc: true
terms: true
title: "checked_mul · moxie function"
---

# `checked_mul`

<p class="specref"><a href="../reference.html#fn-checked_mul">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn checked_mul[T](a T, b T) Result[T, Error]
```

## Description {#description}

Multiplication that reports overflow instead of aborting or wrapping.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** `Ok(product)`, or `Err` (code `OUT_OF_RANGE`, message "overflow") if the product doesn't fit the type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> checked_mul(3, 4)
Ok(12)
```

```
> checked_mul(4611686018427387904, 4)
Err(Error(code: 6, message: "overflow"))
```

