---
layout: default
toc: true
terms: true
dialect: gc
title: "nanos · moxie/gc function"
---

# `nanos`

<p class="specref"><a href="../reference.html#fn-nanos">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn nanos(d Duration) Int
```

## Description {#description}

A `Duration` in whole nanoseconds.

**Parameters**

- `d`: a `Duration`.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> nanos(2ms)
2000000
```

