---
layout: default
toc: true
terms: true
title: "millis · moxie function"
---

# `millis`

<p class="specref"><a href="../reference.html#fn-millis">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn millis(d Duration) Int
```

## Description {#description}

A `Duration` in whole milliseconds.

**Parameters**

- `d`: a `Duration`.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> millis(1500ms)
1500
```

```
> millis(2s)
2000
```

