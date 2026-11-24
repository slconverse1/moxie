---
layout: default
toc: true
terms: true
title: "to_instant · moxie function"
---

# `to_instant`

<p class="specref"><a href="../reference.html#fn-to_instant">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn to_instant(t DateTime) Result[Duration, Error]
fn to_instant(t DateTime, zone String) Result[Duration, Error]
```

## Description {#description}

Turns a `DateTime` into a point on the time line (a `Duration` since 1970 UTC). A date and time on its own is ambiguous, because "10:00" is a different moment in each zone, so you pass the zone it is in. Without one, UTC is assumed. A time that doesn't exist in that zone, or exists twice (when clocks change), is an `Err`.

**Parameters**

- `t`: a `DateTime`.
- `zone` (optional): a zone name such as `"Europe/Paris"`.

**Returns** `Ok(Duration)`, or `Err`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> to_instant(parse_iso("1970-01-02T00:00:00") |> unwrap())
Ok(24h)
```

```
> to_instant(parse_iso("2026-11-23T10:00:00") |> unwrap(), "Europe/Paris") |> map_ok((d) -> seconds(d))
Ok(1795424400.0)
```

