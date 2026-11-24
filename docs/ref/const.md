---
layout: default
toc: true
terms: true
title: "const · moxie function"
---

# `const`

<p class="specref"><a href="../reference.html#fn-const">The alphabetical list</a> · <a href="../spec.html#s23">Spec §23</a></p>

## Signature {#signature}

```
fn const[A, B](x A) (B) -> A
```

## Description {#description}

Makes a function that ignores its input and always gives the same value.

**Parameters**

- `x`: the value to give back.

**Returns** a function that takes any argument and returns `x`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> const(7)("anything")
7
```

