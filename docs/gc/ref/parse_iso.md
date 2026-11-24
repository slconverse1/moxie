---
layout: default
toc: true
terms: true
dialect: gc
title: "parse_iso · moxie/gc function"
---

# `parse_iso`

<p class="specref"><a href="../reference.html#fn-parse_iso">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn parse_iso(s String) Result[DateTime, Error]
```

## Description {#description}

Reads a date and time written in the ISO 8601 form.

**Parameters**

- `s`: the text.

**Returns** `Ok(DateTime)`, or `Err` if the text isn't a valid date and time.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> parse_iso("2026-11-23T10:00:00") |> map_ok((t) -> iso(t))
Ok("2026-11-23T10:00:00")
```

```
> parse_iso("tomorrow") |> is_err()
true
```

