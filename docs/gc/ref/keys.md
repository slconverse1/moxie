---
layout: default
toc: true
terms: true
dialect: gc
title: "keys · moxie/gc function"
---

# `keys`

<p class="specref"><a href="../reference.html#fn-keys">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn keys[K, V](d Dict[K, V]) Stream[K]
```

## Description {#description}

The keys of a `Dict`, in the order they were added.

**Parameters**

- `d`: a `Dict`.

**Returns** a `Stream[K]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> Dict("a" -> 1, "b" -> 2) |> keys() |> collect()
List("a", "b")
```

