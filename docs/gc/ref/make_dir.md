---
layout: default
toc: true
terms: true
dialect: gc
title: "make_dir · moxie/gc function"
---

# `make_dir`

<p class="specref"><a href="../reference.html#fn-make_dir">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn make_dir(p String) Result[Unit, Error]
```

## Description {#description}

Makes a folder, with any missing folders above it. It is not an error if the folder is already there.

**Parameters**

- `p`: the path.

**Returns** `Ok(())`, or `Err`.

## Effects {#effects}

**Effect:** parks

**Needs permission:** fs

## Examples {#examples}

```
> q = path_join(temp_dir(), "moxie_ref_dir/a/b")
println(make_dir(q))
println(path_exists(q))
remove_dir(q)
Ok(())
Ok(true)
```

