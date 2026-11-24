---
layout: default
toc: true
terms: true
title: "write_bytes · moxie function"
---

# `write_bytes`

<p class="specref"><a href="../reference.html#fn-write_bytes">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn write_bytes(out Io, data Array[Byte]) Result[Unit, Error]
```

## Description {#description}

Writes raw bytes to an `Io`.

**Parameters**

- `out`: an `Io`.
- `data`: an `Array[Byte]`.

**Returns** `Ok(())`, or `Err`.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> write_bytes(conn, Array(1, 2, 3))
Ok(())
```

