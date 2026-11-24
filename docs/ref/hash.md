---
layout: default
toc: true
terms: true
title: "hash · moxie function"
---

# `hash`

<p class="specref"><a href="../reference.html#fn-hash">The alphabetical list</a> · <a href="../spec.html#s23">Spec §23</a></p>

## Signature {#signature}

```
fn hash[T](x T) Int
```

## Description {#description}

A whole-number fingerprint of any value, equal for equal values. It is stable within a run and shouldn't be stored or relied on across versions; it is not a cryptographic hash.

**Parameters**

- `x`: any value with `==`.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> hash("a") == hash("a")
true
```

```
> hash(List(1, 2)) == hash(List(1, 2))
true
```

