---
layout: default
toc: true
terms: true
title: "now · moxie function"
---

# `now`

<p class="specref"><a href="../reference.html#fn-now">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn now() Duration
```

## Description {#description}

The current wall-clock time, as a `Duration` since 1970-01-01 00:00 UTC. It can jump when the clock is changed, so it is for stamping events and not for measuring how long something took; use `monotonic` for that. Reading the clock uses the system.

**Parameters** none.

**Returns** a `Duration`.

## Effects {#effects}

**Effect:** uses the system

## Examples {#examples}

```
> now()
1.7e9 seconds as a Duration; changes every call
```

