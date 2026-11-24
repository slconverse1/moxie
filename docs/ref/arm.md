---
layout: default
toc: true
terms: true
title: "arm · moxie function"
---

# `arm`

<p class="specref"><a href="../reference.html#fn-arm">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn arm(t Timer, d Duration) Unit
```

## Description {#description}

Restarts a `Timer` so that it fires once, after the given delay.

**Parameters**

- `t`: the `Timer`.
- `d`: the new delay.

**Returns** nothing.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> t = after(1000ms)
arm(t, 10ms)
println(read(t))
Ok(())
```

