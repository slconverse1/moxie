---
layout: default
toc: true
terms: true
title: "is_nan · moxie function"
---

# `is_nan`

<p class="specref"><a href="../reference.html#fn-is_nan">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn is_nan(x Double) Bool
```

## Description {#description}

True if the number is `NAN`, "not a number", such as the result of `0.0 / 0.0`. `NAN` is not equal to anything, itself included, so `==` can't find it.

**Parameters**

- `x`: a `Double`.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> is_nan(0.0 / 0.0)
true
```

```
> is_nan(1.0)
false
```

