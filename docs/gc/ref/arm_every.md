---
layout: default
toc: true
terms: true
dialect: gc
title: "arm_every · moxie/gc function"
---

# `arm_every`

<p class="specref"><a href="../reference.html#fn-arm_every">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn arm_every(t Timer, d Duration) Unit
```

## Description {#description}

Makes a `Timer` fire repeatedly, once every interval, until it is disarmed.

**Parameters**

- `t`: the `Timer`.
- `d`: the interval.

**Returns** nothing.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> t = after(1000ms)
arm_every(t, 5ms)
read(t)
read(t)
disarm(t)
println("ticked twice")
ticked twice
```

