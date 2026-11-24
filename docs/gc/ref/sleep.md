---
layout: default
toc: true
terms: true
dialect: gc
title: "sleep · moxie/gc function"
---

# `sleep`

<p class="specref"><a href="../reference.html#fn-sleep">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn sleep(d Duration) Unit
```

## Description {#description}

Pauses the current fiber for a while. Other fibers keep running.

**Parameters**

- `d`: how long, as a `Duration` such as `100ms`.

**Returns** nothing.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> sleep(5ms)
println("done")
done
```

