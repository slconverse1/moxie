---
layout: default
toc: true
terms: true
title: "seconds · moxie function"
---

# `seconds`

<p class="specref"><a href="../reference.html#fn-seconds">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn seconds(d Duration) Double
```

## Description {#description}

A `Duration` in seconds, with a fraction.

**Parameters**

- `d`: a `Duration`.

**Returns** a `Double`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> seconds(1500ms)
1.5
```

```
> seconds(2s)
2.0
```

