---
layout: default
toc: true
terms: true
title: "random_int · moxie function"
---

# `random_int`

<p class="specref"><a href="../reference.html#fn-random_int">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn random_int(r Range) Int
```

## Description {#description}

A random whole number chosen uniformly from a range. The call aborts if the range is empty or endless.

**Parameters**

- `r`: a range such as `1..6` (both ends included) or `0..<10`; a step is allowed: `1..9 step 2`.

**Returns** an `Int` in the range.

## Effects {#effects}

**Effect:** uses the system

## Examples {#examples}

```
> random_int(5..5)
5
```

```
> random_int(1..6)
4  (any of 1 to 6)
```

