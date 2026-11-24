---
layout: default
toc: true
terms: true
dialect: gc
title: "group_by · moxie/gc function"
---

# `group_by`

<p class="specref"><a href="../reference.html#fn-group_by">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn group_by[T, K](f (T) -> K, xs Seq[T]) Dict[K, List[T]]
```

## Description {#description}

Collects the items into a `Dict` from key to the list of items with that key. Keys appear in the order they were first seen, and each list keeps the original order.

**Parameters**

- `f`: a function from an item to its key.
- `xs`: the items.

**Returns** a `Dict[K, List[T]]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List("ann", "bo", "cy", "dee") |> group_by((s) -> len(s))
Dict(3 -> List("ann", "dee"), 2 -> List("bo", "cy"))
```

