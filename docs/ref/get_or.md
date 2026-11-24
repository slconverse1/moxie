---
layout: default
toc: true
terms: true
title: "get_or · moxie function"
---

# `get_or`

<p class="specref"><a href="../reference.html#fn-get_or">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn get_or[T, E](r Result[T, E], d T) T
fn get_or[T](o Option[T], d T) T
fn get_or[K, V](d Dict[K, V], k K, d2 V) V
fn get_or[T](xs List[T], i Int, d T) T
```

## Description {#description}

The value you ask for, or `default` when it is not there. It works on a `Result` (an `Err` gives the default), an `Option` (`None` gives the default), a `Dict` (a missing key) and a `List` (a position out of range).

**Parameters**

- the first argument: the `Result`, `Option`, `Dict` or `List` to look in.
- for a `Dict`, the key; for a `List`, the position.
- the last argument: the default, of the same type as the values.

**Returns** the value, or the default.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> get_or(Some(2), 5)
2
```

```
> get_or(None, 5)
5
```

```
> get_or(Err(Error(1, "x")), 5)
5
```

```
> get_or(Dict("a" -> 1), "z", 0)
0
```

```
> get_or(List(1, 2, 3), 9, 0)
0
```

