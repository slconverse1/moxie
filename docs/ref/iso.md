---
layout: default
toc: true
terms: true
title: "iso · moxie function"
---

# `iso`

<p class="specref"><a href="../reference.html#fn-iso">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn iso(t DateTime) String
```

## Description {#description}

Writes a date and time in the ISO 8601 form.

**Parameters**

- `t`: a `DateTime`.

**Returns** a `String` such as `2026-11-23T10:00:00`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> iso(parse_iso("2026-11-23T10:00:00") |> unwrap())
"2026-11-23T10:00:00"
```

