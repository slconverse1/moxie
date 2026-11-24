---
layout: default
toc: true
terms: true
title: "contains · moxie function"
---

# `contains`

<p class="specref"><a href="../reference.html#fn-contains">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn contains(s String, t String) Bool
fn contains[T Equatable](xs Seq[T], x T) Bool
fn contains[K, V](d Dict[K, V], k K) Bool
```

## Description {#description}

True if a collection holds an item, or a `String` holds a piece of text. For a `Dict` it asks about keys, and for a `Set` about members. Items need `==`.

**Parameters**

- `xs`: a `String`, a `List`/`Array`/`Set`/`Ring`/`Stream` or a `Dict`.
- the second argument: the text, the item or the key to look for.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> contains("hello", "ell")
true
```

```
> contains(List(1, 2), 2)
true
```

```
> contains(Dict("a" -> 1), "a")
true
```

```
> contains(Set(1, 2), 3)
false
```

