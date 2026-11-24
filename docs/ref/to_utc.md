---
layout: default
toc: true
terms: true
title: "to_utc · moxie function"
---

# `to_utc`

<p class="specref"><a href="../reference.html#fn-to_utc">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn to_utc(d Duration) DateTime
```

## Description {#description}

The date and time, as the calendar and clock show it in UTC, for a point on the time line.

**Parameters**

- `d`: a `Duration` since 1970 UTC, such as from `now()`.

**Returns** a `DateTime`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> iso(to_utc(86400s))
"1970-01-02T00:00:00"
```

