---
layout: default
toc: true
terms: true
title: "swap_vals · moxie function"
---

# `swap_vals`

<p class="specref"><a href="../reference.html#fn-swap_vals">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn swap_vals[T](a Atom[T], f (T) -> T) (T, T)
```

## Description {#description}

Like `swap`, but returns both the old and the new value, so you can tell what you replaced.

**Parameters**

- `a`: the `Atom`.
- `f`: a function from the old value to the new one.

**Returns** a pair `(old, new)`.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> a = Atom(1)
println(swap_vals(a, (x) -> x + 1))
(1, 2)
```

