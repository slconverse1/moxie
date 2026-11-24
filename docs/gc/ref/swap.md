---
layout: default
toc: true
terms: true
dialect: gc
title: "swap · moxie/gc function"
---

# `swap`

<p class="specref"><a href="../reference.html#fn-swap">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn swap[T](a Atom[T], f (T) -> T) T
```

## Description {#description}

Changes an `Atom` by applying a function to its value, and stores the result. Atoms are changed with one call that reads and writes together, so two fibers can't lose each other's updates. The function may run more than once if another fiber changes the atom meanwhile, so it should have no side effects.

**Parameters**

- `a`: the `Atom`.
- `f`: a function from the old value to the new one.

**Returns** the new value.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> a = Atom(1)
println(swap(a, (x) -> x + 1))
println(@a)
2
2
```

