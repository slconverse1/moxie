---
layout: default
toc: true
terms: true
dialect: gc
title: "fmap · moxie/gc function"
---

# `fmap`

<p class="specref"><a href="../reference.html#fn-fmap">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn fmap[T, U](f (T) -> U, xs List[T]) List[U]
fn fmap[T, U, N](f (T) -> U, xs Array[T][N]) Array[U][N]
fn fmap[T, U](f (T) -> U, o Option[T]) Option[U]
fn fmap[T, U](f (T) -> U, r Result[T, Error]) Result[U, Error]
```

## Description {#description}

Like `map`, but the result has the same shape as the source: a `List` stays a `List`, an `Array` stays an `Array` of the same size, and an `Option` or `Result` stays an `Option` or `Result`. Use `fmap` when you want a collection back and not a stream.

**Parameters**

- `f`: the function to apply to each item.
- `xs`: the `List`, `Array`, `Option` or `Result` to transform.

**Returns** a value of the same kind as `xs`, with each item replaced by `f` of it.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> fmap((x) -> x * 2, List(1, 2, 3))
List(2, 4, 6)
```

```
> fmap((x) -> x + 1, Some(4))
Some(5)
```

