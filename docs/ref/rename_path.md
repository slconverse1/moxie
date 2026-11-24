---
layout: default
toc: true
terms: true
title: "rename_path · moxie function"
---

# `rename_path`

<p class="specref"><a href="../reference.html#fn-rename_path">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn rename_path(a String, b String) Result[Unit, Error]
```

## Description {#description}

Renames or moves a file or folder. If the new name already exists as a file, it is replaced.

**Parameters**

- `a`: the current path.
- `b`: the new path.

**Returns** `Ok(())`, or `Err`.

## Effects {#effects}

**Effect:** parks

**Needs permission:** fs

## Examples {#examples}

```
> a = path_join(temp_dir(), "moxie_ref_a.txt")
b = path_join(temp_dir(), "moxie_ref_b.txt")
write_file(a, "x")
println(rename_path(a, b))
println(path_exists(a))
println(path_exists(b))
remove_file(b)
Ok(())
Ok(false)
Ok(true)
```

