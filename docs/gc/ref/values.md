---
layout: default
toc: true
terms: true
dialect: gc
title: "values · moxie/gc function"
---

# `values`

<p class="specref"><a href="../reference.html#fn-values">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn values[K, V](d Dict[K, V]) Stream[V]
```

## Description {#description}

The values of a `Dict`, in the order their keys were added. Not to be confused with the `values()` helper that an enum has, which lists its cases.

**Parameters**

- `d`: a `Dict`.

**Returns** a `Stream[V]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> Dict("a" -> 1, "b" -> 2) |> values() |> collect()
List(1, 2)
```

