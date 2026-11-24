---
layout: default
toc: true
terms: true
dialect: gc
title: "remove_at · moxie/gc function"
---

# `remove_at`

<p class="specref"><a href="../reference.html#fn-remove_at">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn remove_at[T](xs List[T], i Int) List[T]
fn remove_at[T](xs Array[T], i Int) Array[T]
```

## Description {#description}

A copy without the item at a position. The position must exist, or the call aborts.

**Parameters**

- `xs`: a `List` or `Array`.
- `i`: the position, counting from 0.

**Returns** the shorter collection.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> remove_at(List(5, 6, 7), 1)
List(5, 7)
```

