---
layout: default
toc: true
terms: true
dialect: gc
title: "read_file · moxie/gc function"
---

# `read_file`

<p class="specref"><a href="../reference.html#fn-read_file">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn read_file(p String) Result[String, Error]
```

## Description {#description}

Reads a whole text file into a `String`. A file that is missing, unreadable or not valid UTF-8 is an `Err`, never an abort.

**Parameters**

- `p`: the path.

**Returns** `Ok(text)`, or `Err` (code `NOT_FOUND` if there is no such file).

## Effects {#effects}

**Effect:** parks

**Needs permission:** fs

## Examples {#examples}

```
> p = path_join(temp_dir(), "moxie_ref_demo.txt")
write_file(p, "hello")
println(read_file(p))
remove_file(p)
Ok("hello")
```

```
> read_file("/no/such/file") |> is_err()
true
```

