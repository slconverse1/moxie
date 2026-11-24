---
layout: default
toc: true
terms: true
title: "read_bytes · moxie function"
---

# `read_bytes`

<p class="specref"><a href="../reference.html#fn-read_bytes">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn read_bytes(src Io, n Int) Result[Array[Byte], Error]
```

## Description {#description}

Reads up to `n` bytes from an `Io`. At the end of the input you get fewer than `n`, or none.

**Parameters**

- `src`: an `Io`.
- `n`: how many bytes at most.

**Returns** `Ok(bytes)` as an `Array[Byte]`, or `Err`.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> read_bytes(conn, 4)
Ok(Array(1, 2, 3, 4))
```

