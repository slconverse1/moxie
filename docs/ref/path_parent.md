---
layout: default
toc: true
terms: true
title: "path_parent · moxie function"
---

# `path_parent`

<p class="specref"><a href="../reference.html#fn-path_parent">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn path_parent(p String) String
```

## Description {#description}

Everything but the last part of a path: the folder that holds it.

**Parameters**

- `p`: a path.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> path_parent("/a/b/c.txt")
"/a/b"
```

```
> path_parent("c.txt")
""
```

