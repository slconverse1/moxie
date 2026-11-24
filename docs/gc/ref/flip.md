---
layout: default
toc: true
terms: true
dialect: gc
title: "flip · moxie/gc function"
---

# `flip`

<p class="specref"><a href="../reference.html#fn-flip">The alphabetical list</a> · <a href="../spec.html#s23">Spec §23</a></p>

## Signature {#signature}

```
fn flip[A, B, R](f (A, B) -> R) (B, A) -> R
```

## Description {#description}

Makes a version of a two-argument function that takes its arguments in the opposite order.

**Parameters**

- `f`: a function of two arguments.

**Returns** a function `g` with `g(b, a) == f(a, b)`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> flip((a, b) -> a - b)(1, 10)
9
```

