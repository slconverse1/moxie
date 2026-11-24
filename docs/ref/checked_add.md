---
layout: default
toc: true
terms: true
title: "checked_add · moxie function"
---

# `checked_add`

<p class="specref"><a href="../reference.html#fn-checked_add">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn checked_add[T](a T, b T) Result[T, Error]
```

## Description {#description}

Addition that reports overflow instead of aborting or wrapping. Use it when the numbers come from outside and might be too big.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** `Ok(sum)`, or `Err` (code `OUT_OF_RANGE`, message "overflow") if the sum doesn't fit the type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> checked_add(1, 2)
Ok(3)
```

```
> checked_add(9223372036854775807, 1)
Err(Error(code: 6, message: "overflow"))
```

