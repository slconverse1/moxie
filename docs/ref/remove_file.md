---
layout: default
toc: true
terms: true
title: "remove_file · moxie function"
---

# `remove_file`

<p class="specref"><a href="../reference.html#fn-remove_file">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn remove_file(p String) Result[Unit, Error]
```

## Description {#description}

Deletes a file. A missing file is an `Err`.

**Parameters**

- `p`: the path.

**Returns** `Ok(())`, or `Err` (code `NOT_FOUND` if there was no such file).

## Effects {#effects}

**Effect:** parks

**Needs permission:** fs

## Examples {#examples}

```
> p = path_join(temp_dir(), "moxie_ref_demo.txt")
write_file(p, "x")
println(remove_file(p))
println(path_exists(p))
Ok(())
Ok(false)
```

