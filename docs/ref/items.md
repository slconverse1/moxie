---
layout: default
toc: true
terms: true
title: "items · moxie function"
---

# `items`

<p class="specref"><a href="../reference.html#fn-items">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn items[K, V](d Dict[K, V]) Stream[(K, V)]
```

## Description {#description}

The key and value pairs of a `Dict`, in the order the keys were added. In a `for`, two names take each pair apart: `for k, v in d |> items()`.

**Parameters**

- `d`: a `Dict`.

**Returns** a `Stream[(K, V)]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> Dict("a" -> 1, "b" -> 2) |> items() |> collect()
List(("a", 1), ("b", 2))
```

