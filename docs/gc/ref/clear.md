---
layout: default
toc: true
terms: true
dialect: gc
title: "clear · moxie/gc function"
---

# `clear`

<p class="specref"><a href="../reference.html#fn-clear">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn clear[K, V](d Dict[K, V]) Dict[K, V]
fn clear[T](s Set[T]) Set[T]
fn clear[T](xs List[T]) List[T]
```

## Description {#description}

An empty collection of the same kind and type, with the same capacity.

**Parameters**

- `xs`: a `Dict`, `Set` or `List`.

**Returns** the empty collection.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> clear(Dict("a" -> 1))
Dict()
```

```
> clear(List(1, 2))
List()
```

