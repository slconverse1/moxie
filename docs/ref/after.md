---
layout: default
toc: true
terms: true
title: "after · moxie function"
---

# `after`

<p class="specref"><a href="../reference.html#fn-after">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn after(d Duration) Timer
```

## Description {#description}

Makes a `Timer`, a channel that receives one value after a delay. It is used with `select`, to wait for something but not forever.

**Parameters**

- `d`: how long to wait, as a `Duration` such as `50ms`.

**Returns** a `Timer`.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> t = after(10ms)
println(read(t))
Ok(())
```

