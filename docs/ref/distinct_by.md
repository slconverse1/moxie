---
layout: default
toc: true
terms: true
title: "distinct_by · moxie function"
---

# `distinct_by`

<p class="specref"><a href="../reference.html#fn-distinct_by">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn distinct_by[T, K](f (T) -> K, xs Seq[T]) Stream[T]
```

## Description {#description}

Drops items whose key has already been seen, keeping the first item for each key, in their original order.

**Parameters**

- `f`: a function from an item to its key.
- `xs`: the items.

**Returns** a `Stream[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List("ab", "cd", "e", "f") |> distinct_by((s) -> len(s)) |> collect()
List("ab", "e")
```

