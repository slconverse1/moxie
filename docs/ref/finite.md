---
layout: default
toc: true
terms: true
title: "finite · moxie function"
---

# `finite`

<p class="specref"><a href="../reference.html#fn-finite">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn finite(x Double) Result[Double, Error]
```

## Description {#description}

Checks that a floating-point number is an ordinary number: not infinity and not `NAN`. It turns the "check later" values of floating point into a `Result` you handle now.

**Parameters**

- `x`: a `Double`.

**Returns** `Ok(x)`, or `Err` (code `OUT_OF_RANGE`, message "not finite").

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> finite(1.5)
Ok(1.5)
```

```
> finite(1.0 / 0.0)
Err(Error(code: 6, message: "not finite"))
```

```
> finite(0.0 / 0.0)
Err(Error(code: 6, message: "not finite"))
```

