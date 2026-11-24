---
layout: default
toc: true
terms: true
dialect: gc
title: "div · moxie/gc function"
---

# `div`

<p class="specref"><a href="../reference.html#fn-div">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn div(a Decimal, b Decimal, scale Int, mode Mode) Result[Decimal, Error]
```

## Description {#description}

Divides one `Decimal` by another to a scale you choose. Exact decimal division can have endless digits, so it needs a number of places and a rounding mode. A zero divisor is an `Err`, not an abort.

**Parameters**

- `a`: the dividend.
- `b`: the divisor.
- `scale`: how many decimal places the result has.
- `mode`: `#half_even`, `#half_up` or `#down`.

**Returns** `Ok(quotient)`, or `Err` (code `OUT_OF_RANGE`, message "division by zero").

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> div(10.00d, 3.00d, 4, #half_up)
Ok(3.3333)
```

```
> div(10.00d, 4.00d, 1, #half_even)
Ok(2.5)
```

```
> div(1.0d, 0.0d, 2, #half_up)
Err(Error(code: 6, message: "division by zero"))
```

