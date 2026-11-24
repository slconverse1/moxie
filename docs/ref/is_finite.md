---
layout: default
toc: true
terms: true
title: "is_finite · moxie function"
---

# `is_finite`

<p class="specref"><a href="../reference.html#fn-is_finite">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn is_finite(x Double) Bool
```

## Description {#description}

True if the number is neither infinity nor `NAN`.

**Parameters**

- `x`: a `Double`.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> is_finite(1.0)
true
```

```
> is_finite(1.0 / 0.0)
false
```

