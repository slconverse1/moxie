---
layout: default
toc: true
terms: true
title: "len · moxie function"
---

# `len`

<p class="specref"><a href="../reference.html#fn-len">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn len(s String) Int
fn len[T](xs Seq[T]) Int
fn len[K, V](d Dict[K, V]) Int
```

## Description {#description}

How many items a collection holds, or how many bytes a `String` has. A `String` is stored as UTF-8, so a character outside plain ASCII counts as more than one byte; use `char_count` for characters and `grapheme_count` for what a reader sees as one character.

**Parameters**

- `xs`: a `String`, `List`, `Array`, `Set`, `Dict`, `Ring`, `Stream` or other collection.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> len("hello")
5
```

```
> len("héllo")
6
```

```
> len(List(1, 2, 3))
3
```

```
> len(Dict("a" -> 1))
1
```

