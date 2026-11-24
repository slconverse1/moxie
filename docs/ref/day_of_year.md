---
layout: default
toc: true
terms: true
title: "day_of_year · moxie function"
---

# `day_of_year`

<p class="specref"><a href="../reference.html#fn-day_of_year">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn day_of_year(t DateTime) Int
```

## Description {#description}

Which day of the year a date is, counting 1 January as 1.

**Parameters**

- `t`: a `DateTime`.

**Returns** an `Int`, 1 to 366.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> day_of_year(parse_iso("2026-11-23T10:00:00") |> unwrap())
327
```

