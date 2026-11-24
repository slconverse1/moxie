---
layout: default
toc: true
terms: true
title: "pow · moxie function"
---

# `pow`

<p class="specref"><a href="../reference.html#fn-pow">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn pow(a Int, b Int) Int
fn pow(a Double, b Double) Double
```

## Description {#description}

A number raised to a power. With two `Int`s the result is an `Int`; with two floating-point numbers it is a `Double`.

**Parameters**

- `a`: the base.
- `b`: the exponent.

**Returns** `a` to the power `b`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> pow(2, 10)
1024
```

```
> pow(2.0, 0.5)
1.4142135623730951
```

```
> pow(0, 0)
1
```

