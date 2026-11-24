---
layout: default
toc: true
terms: true
title: "file_info · moxie function"
---

# `file_info`

<p class="specref"><a href="../reference.html#fn-file_info">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn file_info(p String) Result[FileInfo, Error]
```

## Description {#description}

Facts about a file or folder: its `kind` (`"file"` or `"dir"`) and its `size` in bytes.

**Parameters**

- `p`: the path.

**Returns** `Ok(FileInfo)`, or `Err` if there is nothing at the path.

## Effects {#effects}

**Effect:** parks

**Needs permission:** fs

## Examples {#examples}

```
> p = path_join(temp_dir(), "moxie_ref_demo.txt")
write_file(p, "hello")
info = file_info(p) |> unwrap()
println(info)
remove_file(p)
FileInfo(kind: "file", size: 5)
```

