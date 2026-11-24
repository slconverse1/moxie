---
layout: default
toc: true
terms: true
title: "set · moxie function"
---

# `set`

<p class="specref"><a href="../reference.html#fn-set">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn set[T](xs List[T], i Int, x T) List[T]
fn set[T](xs Array[T], i Int, x T) Array[T]
fn set[T](xs MultiArray[T], i Int, x T) MultiArray[T]
fn set[K, V](d Dict[K, V], k K, v V) Dict[K, V]
```

## Description {#description}

A copy with one position or key replaced; the original is unchanged. For a `List`, `Array` or `MultiArray`, the position must already exist, or the call aborts; it never makes the collection longer. For a `Dict`, an existing key gets the new value and a new key is added. In moxie (no garbage collector) a `List`, `Set` or `Dict` has a fixed capacity, so adding to a full one aborts; in moxie/gc they grow as needed.

**Parameters**

- `xs`: a `List`, `Array`, `MultiArray` or `Dict`.
- the position or key.
- the new value.

**Returns** the updated collection, of the same kind.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> set(List(1, 2, 3), 1, 9)
List(1, 9, 3)
```

```
> set(Array(1, 2, 3), 0, 9)
Array(9, 2, 3)
```

```
> set(Dict("a" -> 1), "a", 5)
Dict("a" -> 5)
```

