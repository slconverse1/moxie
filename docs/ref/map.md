---
layout: default
toc: true
terms: true
title: "map · moxie function"
---

# `map`

<p class="specref"><a href="../reference.html#fn-map">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn map[T, U](f (T) -> U, xs Seq[T]) Stream[U]
fn map[T, U](f (T) -> U, r Result[T, Error]) Result[U, Error]
fn map[T, U](f (T) -> U, o Option[T]) Option[U]
```

## Description {#description}

Applies `f` to every item and gives the results as a stream. A stream is lazy: nothing is computed until something consumes it, such as `collect`, `sum` or a `for` loop. On a `Result`, `map` changes the value inside an `Ok` and passes an `Err` along; on an `Option`, it changes the value inside a `Some` and passes `None` along.

**Parameters**

- `f`: the function to apply to each item (or to the value inside a `Result` or `Option`).
- `xs`: the items. `Seq[T]` is any source of `T` values: a `List`, `Array`, `Set`, `Ring` or `Stream`.

**Returns** a `Stream[U]` of the results, in the same order; for a `Result` or `Option`, a value of the same kind.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> map((x) -> x * 2) |> collect()
List(2, 4, 6)
```

```
> map((x) -> x + 1, Some(1))
Some(2)
```

```
> map((x) -> x + 1, None)
None
```

```
> map((x) -> x + 1, Ok(1))
Ok(2)
```

```
> map((x) -> x + 1, Err(Error(7, "no")))
Err(Error(code: 7, message: "no"))
```

