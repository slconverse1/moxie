---
layout: default
toc: true
terms: true
title: "to_zone · moxie function"
---

# `to_zone`

<p class="specref"><a href="../reference.html#fn-to_zone">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn to_zone(d Duration, zone String) Result[DateTime, Error]
```

## Description {#description}

The date and time in a named zone, for a point on the time line.

**Parameters**

- `d`: a `Duration` since 1970 UTC.
- `zone`: a zone name such as `"Asia/Tokyo"`.

**Returns** `Ok(DateTime)`, or `Err` if the zone is unknown.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> to_zone(0s, "Asia/Tokyo") |> map_ok((t) -> iso(t))
Ok("1970-01-01T09:00:00")
```

```
> to_zone(0s, "Nowhere/Land") |> is_err()
true
```

