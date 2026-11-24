---
layout: default
toc: true
terms: true
dialect: gc
title: "remove · moxie/gc function"
---

# `remove`

<p class="specref"><a href="../reference.html#fn-remove">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn remove[K, V](d Dict[K, V], k K) Dict[K, V]
fn remove[T](s Set[T], x T) Set[T]
fn remove[T](xs List[T], x T) List[T]
fn remove[T](xs Array[T], x T) Array[T]
```

## Description {#description}

A copy without one item. For a `Dict` the item is a key, for a `Set` a member, and for a `List` or `Array` the first item equal to it. If it is not there, the collection comes back unchanged.

**Parameters**

- `xs`: a `Dict`, `Set`, `List` or `Array`.
- the key or item to leave out.

**Returns** the smaller collection, of the same kind.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> remove(Dict("a" -> 1, "b" -> 2), "a")
Dict("b" -> 2)
```

```
> remove(Set(1, 2), 1)
Set(2)
```

```
> remove(List(1, 2, 1), 1)
List(2, 1)
```

```
> remove(List(1, 2), 9)
List(1, 2)
```

