---
layout: default
toc: true
terms: true
title: "list_dir · moxie function"
---

# `list_dir`

<p class="specref"><a href="../reference.html#fn-list_dir">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn list_dir(p String) Result[Array[String], Error]
```

## Description {#description}

The names of the items in a folder, sorted, without the folder's own path.

**Parameters**

- `p`: the path of a folder.

**Returns** `Ok(names)` as an `Array[String]`, or `Err`.

## Effects {#effects}

**Effect:** parks

**Needs permission:** fs

## Examples {#examples}

```
> q = path_join(temp_dir(), "moxie_ref_dir3")
make_dir(q)
write_file(path_join(q, "b.txt"), "")
write_file(path_join(q, "a.txt"), "")
println(list_dir(q))
remove_file(path_join(q, "a.txt"))
remove_file(path_join(q, "b.txt"))
remove_dir(q)
Ok(Array("a.txt", "b.txt"))
```

