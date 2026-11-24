---
layout: default
toc: true
terms: true
title: "ceil · moxie function"
---

# `ceil`

<p class="specref"><a href="../reference.html#fn-ceil">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn ceil(x Double) Int
```

## Description {#description}

Rounds up, towards positive infinity, to a whole number.

**Parameters**

- `x`: a floating-point number.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> ceil(2.1)
3
```

```
> ceil(-2.9)
-2
```

