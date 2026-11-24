---
layout: default
toc: true
terms: true
title: "path_exists · moxie function"
---

# `path_exists`

<p class="specref"><a href="../reference.html#fn-path_exists">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn path_exists(p String) Result[Bool, Error]
```

## Description {#description}

Whether a file or folder is there. Asking can fail, for instance when a folder above it can't be read, which is why the answer is a `Result`.

**Parameters**

- `p`: the path.

**Returns** `Ok(true)`, `Ok(false)`, or `Err`.

## Effects {#effects}

**Effect:** parks

**Needs permission:** fs

## Examples {#examples}

```
> path_exists("/no/such/file")
Ok(false)
```

