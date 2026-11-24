---
layout: default
toc: true
terms: true
dialect: gc
title: "remove_dir · moxie/gc function"
---

# `remove_dir`

<p class="specref"><a href="../reference.html#fn-remove_dir">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn remove_dir(p String) Result[Unit, Error]
```

## Description {#description}

Deletes a folder. The folder has to be empty; this is deliberate, so one call can't wipe out a tree by mistake.

**Parameters**

- `p`: the path.

**Returns** `Ok(())`, or `Err`.

## Effects {#effects}

**Effect:** parks

**Needs permission:** fs

## Examples {#examples}

```
> q = path_join(temp_dir(), "moxie_ref_dir2")
make_dir(q)
println(remove_dir(q))
println(path_exists(q))
Ok(())
Ok(false)
```

