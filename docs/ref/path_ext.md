---
layout: default
toc: true
terms: true
title: "path_ext · moxie function"
---

# `path_ext`

<p class="specref"><a href="../reference.html#fn-path_ext">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn path_ext(p String) String
```

## Description {#description}

The extension of the file name, without the dot, or an empty `String` if there is none.

**Parameters**

- `p`: a path.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> path_ext("/a/b/c.txt")
"txt"
```

```
> path_ext("archive.tar.gz")
"gz"
```

```
> path_ext("Makefile")
""
```

