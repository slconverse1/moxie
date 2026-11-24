---
layout: default
toc: true
terms: true
dialect: gc
title: "format_time · moxie/gc function"
---

# `format_time`

<p class="specref"><a href="../reference.html#fn-format_time">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn format_time(t DateTime, fmt String) String
fn format_time(t DateTime, fmt String, loc Locale) String
```

## Description {#description}

Writes a date and time using a pattern. `%Y` year, `%m` month, `%d` day, `%H` hour, `%M` minute, `%S` second, `%A` the weekday name, `%B` the month name. With a `Locale`, names such as `%A` and `%B` are in that language.

**Parameters**

- `t`: a `DateTime`.
- `fmt`: the pattern.
- `loc` (optional): a `Locale`.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> format_time(parse_iso("2026-11-23T10:00:00") |> unwrap(), "%d/%m/%Y %H:%M")
"23/11/2026 10:00"
```

```
> format_time(parse_iso("2026-11-23T10:00:00") |> unwrap(), "%A %d %B %Y")
"Monday 23 November 2026"
```

```
> format_time(parse_iso("2026-11-23T10:00:00") |> unwrap(), "%A %d %B %Y", Locale.de_de)
"Montag 23 November 2026"
```

