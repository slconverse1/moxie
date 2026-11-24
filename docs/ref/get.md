---
layout: default
toc: true
terms: true
title: "get · moxie function"
---

# `get`

<p class="specref"><a href="../reference.html#fn-get">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn get[K, V](d Dict[K, V], k K) Result[V, Error]
fn get[T](xs List[T], i Int) Result[T, Error]
fn get[T](xs Array[T], i Int) Result[T, Error]
```

## Description {#description}

The item at a position or key, as a `Result`, so that a missing item is something the caller has to deal with and not a crash. To fall back to a default instead, use `get_or`. For a list or array, `xs(i)` reads a position directly and aborts if it is out of range.

**Parameters**

- `xs`: a `List`, `Array` or `Dict`.
- `i` or `k`: the position (counting from 0) or the key.

**Returns** `Ok(item)`, or `Err` with the code `MISSING` ("no such element" for a position, "no such key" for a key).

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> get(List(10, 20, 30), 1)
Ok(20)
```

```
> get(List(10, 20, 30), 9)
Err(Error(code: 4, message: "no such element"))
```

```
> get(Dict("a" -> 1), "a")
Ok(1)
```

```
> get(Dict("a" -> 1), "b")
Err(Error(code: 4, message: "no such key"))
```

