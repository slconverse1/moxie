---
layout: default
toc: true
terms: true
dialect: gc
title: "monotonic · moxie/gc function"
---

# `monotonic`

<p class="specref"><a href="../reference.html#fn-monotonic">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn monotonic() Duration
```

## Description {#description}

A clock that only goes forward, for measuring elapsed time. Its zero is arbitrary; only differences between two readings mean anything.

**Parameters** none.

**Returns** a `Duration`.

## Effects {#effects}

**Effect:** uses the system

## Examples {#examples}

```
> monotonic() - start
the time that has passed since `start = monotonic()`
```

