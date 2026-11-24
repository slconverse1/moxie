---
layout: default
toc: true
terms: true
title: "path_join · moxie function"
---

# `path_join`

<p class="specref"><a href="../reference.html#fn-path_join">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn path_join(base String, rest String) String
```

## Description {#description}

Joins two parts of a path with the right separator. If the second part is an absolute path, it wins.

**Parameters**

- `base`: the first part.
- `rest`: the second part.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> path_join("a", "b.txt")
"a/b.txt"
```

```
> path_join("a/", "b.txt")
"a/b.txt"
```

```
> path_join("a", "/etc/x")
"/etc/x"
```

