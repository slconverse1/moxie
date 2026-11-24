---
layout: default
toc: true
terms: true
dialect: gc
title: "path_name · moxie/gc function"
---

# `path_name`

<p class="specref"><a href="../reference.html#fn-path_name">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn path_name(p String) String
```

## Description {#description}

The last part of a path: the file or folder name.

**Parameters**

- `p`: a path.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> path_name("/a/b/c.txt")
"c.txt"
```

```
> path_name("c.txt")
"c.txt"
```

