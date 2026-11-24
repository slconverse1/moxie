---
layout: default
toc: true
terms: true
title: "weekday · moxie function"
---

# `weekday`

<p class="specref"><a href="../reference.html#fn-weekday">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn weekday(t DateTime) Int
```

## Description {#description}

The day of the week of a date and time.

**Parameters**

- `t`: a `DateTime`.

**Returns** an `Int`, 1 for Monday up to 7 for Sunday.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> weekday(parse_iso("2026-11-23T10:00:00") |> unwrap())
1
```

```
> weekday(parse_iso("2026-11-22T10:00:00") |> unwrap())
7
```

