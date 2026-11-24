---
layout: default
toc: true
terms: true
title: "sqrt · moxie function"
---

# `sqrt`

<p class="specref"><a href="../reference.html#fn-sqrt">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn sqrt(x Double) Double
```

## Description {#description}

The square root. The square root of a negative number is `NAN`, which is not an error; test for it with `is_nan`, or use `finite`.

**Parameters**

- `x`: a number.

**Returns** a `Double`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> sqrt(16.0)
4.0
```

```
> sqrt(2)
1.4142135623730951
```

```
> sqrt(-1.0)
NAN
```

