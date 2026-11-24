---
layout: default
toc: true
terms: true
dialect: gc
title: "path_stem · moxie/gc function"
---

# `path_stem`

<p class="specref"><a href="../reference.html#fn-path_stem">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn path_stem(p String) String
```

## Description {#description}

The file name without its extension.

**Parameters**

- `p`: a path.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> path_stem("/a/b/c.txt")
"c"
```

```
> path_stem("archive.tar.gz")
"archive.tar"
```

