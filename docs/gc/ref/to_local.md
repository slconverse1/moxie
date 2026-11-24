---
layout: default
toc: true
terms: true
dialect: gc
title: "to_local · moxie/gc function"
---

# `to_local`

<p class="specref"><a href="../reference.html#fn-to_local">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn to_local(d Duration) DateTime
```

## Description {#description}

The date and time in the computer's own time zone, for a point on the time line.

**Parameters**

- `d`: a `Duration` since 1970 UTC.

**Returns** a `DateTime`.

## Effects {#effects}

**Effect:** uses the system

## Examples {#examples}

```
> to_local(now())
the current local date and time
```

