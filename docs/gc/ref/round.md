---
layout: default
toc: true
terms: true
dialect: gc
title: "round · moxie/gc function"
---

# `round`

<p class="specref"><a href="../reference.html#fn-round">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn round(x Double) Int
```

## Description {#description}

Rounds to the nearest whole number. A number exactly halfway rounds up, towards positive infinity, so 2.5 gives 3 and -2.5 gives -2.

**Parameters**

- `x`: a floating-point number.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> round(2.4)
2
```

```
> round(2.5)
3
```

```
> round(-2.5)
-2
```

```
> round(3.5)
4
```

