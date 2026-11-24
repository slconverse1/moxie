---
layout: default
toc: true
terms: true
title: "is_inf · moxie function"
---

# `is_inf`

<p class="specref"><a href="../reference.html#fn-is_inf">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn is_inf(x Double) Bool
```

## Description {#description}

True if the number is positive or negative infinity, such as `1.0 / 0.0`.

**Parameters**

- `x`: a `Double`.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> is_inf(1.0 / 0.0)
true
```

```
> is_inf(-1.0 / 0.0)
true
```

```
> is_inf(1.0)
false
```

