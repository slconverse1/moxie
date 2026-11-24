---
layout: default
toc: true
terms: true
dialect: gc
title: "reset_vals · moxie/gc function"
---

# `reset_vals`

<p class="specref"><a href="../reference.html#fn-reset_vals">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn reset_vals[T](a Atom[T], v T) (T, T)
```

## Description {#description}

Like `reset`, but returns both the old and the new value.

**Parameters**

- `a`: the `Atom`.
- `v`: the new value.

**Returns** a pair `(old, new)`.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> a = Atom(1)
println(reset_vals(a, 9))
(1, 9)
```

