---
layout: default
toc: true
terms: true
title: "write_file · moxie function"
---

# `write_file`

<p class="specref"><a href="../reference.html#fn-write_file">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn write_file(p String, s String) Result[Unit, Error]
```

## Description {#description}

Writes text to a file, replacing whatever was there, and creating the file if needed. The folder must already exist; see `make_dir`.

**Parameters**

- `p`: the path.
- `s`: the text.

**Returns** `Ok(())`, or `Err`.

## Effects {#effects}

**Effect:** parks

**Needs permission:** fs

## Examples {#examples}

```
> p = path_join(temp_dir(), "moxie_ref_demo.txt")
println(write_file(p, "hi"))
remove_file(p)
Ok(())
```

