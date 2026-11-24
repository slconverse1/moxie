---
layout: default
toc: true
terms: true
dialect: gc
title: "random · moxie/gc function"
---

# `random`

<p class="specref"><a href="../reference.html#fn-random">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn random() Double
```

## Description {#description}

A random `Double` from 0 up to, but not including, 1. Random numbers come from the system's generator, so a program that uses them uses the system.

**Parameters** none.

**Returns** a `Double`.

## Effects {#effects}

**Effect:** uses the system

## Examples {#examples}

```
> random() < 1.0
true
```

```
> random()
0.7236...  (a different number each time)
```

