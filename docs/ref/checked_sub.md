---
layout: default
toc: true
terms: true
title: "checked_sub · moxie function"
---

# `checked_sub`

<p class="specref"><a href="../reference.html#fn-checked_sub">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn checked_sub[T](a T, b T) Result[T, Error]
```

## Description {#description}

Subtraction that reports overflow instead of aborting or wrapping.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** `Ok(a - b)`, or `Err` (code `OUT_OF_RANGE`, message "overflow") if the result doesn't fit the type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> checked_sub(1, 2)
Ok(-1)
```

```
> checked_sub(cast[UInt8](1), cast[UInt8](2))
Err(Error(code: 6, message: "overflow"))
```

