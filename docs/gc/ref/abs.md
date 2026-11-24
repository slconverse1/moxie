---
layout: default
toc: true
terms: true
dialect: gc
title: "abs · moxie/gc function"
---

# `abs`

<p class="specref"><a href="../reference.html#fn-abs">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn abs(n Int) Int
fn abs(x Double) Double
```

## Description {#description}

The absolute value: a number without its sign. For a fixed-width integer, the most negative value has no positive twin, so `abs` of it aborts.

**Parameters**

- `n`: an integer or a floating-point number.

**Returns** a number of the same type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> abs(-3)
3
```

```
> abs(2.5)
2.5
```

```
> abs(-2.5)
2.5
```

