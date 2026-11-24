---
layout: default
toc: true
terms: true
dialect: gc
title: "is_empty · moxie/gc function"
---

# `is_empty`

<p class="specref"><a href="../reference.html#fn-is_empty">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn is_empty(s String) Bool
fn is_empty[T](xs Seq[T]) Bool
fn is_empty[K, V](d Dict[K, V]) Bool
fn is_empty[T](s Set[T]) Bool
```

## Description {#description}

True when a `String` or collection has no items.

**Parameters**

- `xs`: a `String`, `List`, `Array`, `Set`, `Dict` or other collection.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> is_empty("")
true
```

```
> is_empty(List(1))
false
```

```
> is_empty(List())
true
```

