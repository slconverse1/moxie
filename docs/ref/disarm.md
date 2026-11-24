---
layout: default
toc: true
terms: true
title: "disarm · moxie function"
---

# `disarm`

<p class="specref"><a href="../reference.html#fn-disarm">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn disarm(t Timer) Unit
```

## Description {#description}

Stops a `Timer` from firing. A timer that is not running is left as it is.

**Parameters**

- `t`: the `Timer`.

**Returns** nothing.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> t = after(1000ms)
disarm(t)
println("disarmed")
disarmed
```

