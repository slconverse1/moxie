---
layout: default
toc: true
terms: true
title: "parse_time · moxie function"
---

# `parse_time`

<p class="specref"><a href="../reference.html#fn-parse_time">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn parse_time(s String, fmt String) Result[DateTime, Error]
fn parse_time(s String, fmt String, loc Locale) Result[DateTime, Error]
```

## Description {#description}

Reads a date and time written in any pattern, with the same codes that `format_time` writes.

**Parameters**

- `s`: the text.
- `fmt`: the pattern.
- `loc` (optional): a `Locale`, for month and day names.

**Returns** `Ok(DateTime)`, or `Err` if the text doesn't match.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> parse_time("23/11/2026", "%d/%m/%Y") |> map_ok((t) -> iso(t))
Ok("2026-11-23T00:00:00")
```

```
> parse_time("nonsense", "%d/%m/%Y") |> is_err()
true
```

