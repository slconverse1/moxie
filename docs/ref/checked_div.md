---
layout: default
toc: true
terms: true
title: "checked_div · moxie function"
---

# `checked_div`

<p class="specref"><a href="../reference.html#fn-checked_div">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn checked_div[T](a T, b T) Result[T, Error]
```

## Description {#description}

Division that reports a zero divisor, and overflow, instead of aborting. Integer division rounds towards zero.

**Parameters**

- `a`: the dividend.
- `b`: the divisor.

**Returns** `Ok(quotient)`, or `Err` (code `OUT_OF_RANGE`, message "division by zero") when `b` is 0.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> checked_div(7, 2)
Ok(3)
```

```
> checked_div(7, 0)
Err(Error(code: 6, message: "division by zero"))
```

