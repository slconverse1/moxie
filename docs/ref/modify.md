---
layout: default
toc: true
terms: true
title: "modify · moxie function"
---

# `modify`

<p class="specref"><a href="../reference.html#fn-modify">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn modify[T, P, A](x T, path P, f (A) -> A) T
```

## Description {#description}

A copy of a value with the part at a data path changed by a function. It is `replace` where the new value is computed from the old one.

**Parameters**

- `x`: the value to update.
- `path`: a data path such as `/User/firm/floor`.
- `f`: a function from the old part to the new one; a placeholder works too: `_ + 1`.

**Returns** the updated copy.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> modify(a, /User/firm/floor, _ + 1)
a copy of `a` whose firm is one floor higher
```

