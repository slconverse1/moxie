---
layout: default
toc: true
terms: true
dialect: gc
title: "floor · moxie/gc function"
---

# `floor`

<p class="specref"><a href="../reference.html#fn-floor">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn floor(x Double) Int
```

## Description {#description}

Rounds down, towards negative infinity, to a whole number.

**Parameters**

- `x`: a floating-point number.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> floor(2.7)
2
```

```
> floor(-2.1)
-3
```

```
> floor(7)
7
```

