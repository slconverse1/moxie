---
layout: default
toc: true
terms: true
title: "replace · moxie function"
---

# `replace`

<p class="specref"><a href="../reference.html#fn-replace">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn replace[T, P, V](x T, path P, v V) T
```

## Description {#description}

A copy of a value with the part at a data path replaced. The path says where to go: `/User/firm/name` is the `name` field of the `firm` field of a `User`. The value you pass in is unchanged. Paths are checked when the program is compiled, so a path that doesn't exist is an error.

**Parameters**

- `x`: the value to update (a tuple, or something containing tuples).
- `path`: a data path.
- `v`: the new value.

**Returns** the updated copy.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> replace(a, /User/firm/name, "Acme")
a copy of `a` whose firm is named Acme
```

