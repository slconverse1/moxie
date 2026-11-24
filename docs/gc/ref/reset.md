---
layout: default
toc: true
terms: true
dialect: gc
title: "reset · moxie/gc function"
---

# `reset`

<p class="specref"><a href="../reference.html#fn-reset">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn reset[T](a Atom[T], v T) T
```

## Description {#description}

Replaces the value of an `Atom` outright.

**Parameters**

- `a`: the `Atom`.
- `v`: the new value.

**Returns** the new value.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> a = Atom(1)
println(reset(a, 9))
println(@a)
9
9
```

