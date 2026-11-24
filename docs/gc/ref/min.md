---
layout: default
toc: true
terms: true
dialect: gc
title: "min · moxie/gc function"
---

# `min`

<p class="specref"><a href="../reference.html#fn-min">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn min[T Ordered](a T, b T) T
fn min[T Ordered](xs Seq[T]) Result[T, Error]
```

## Description {#description}

The smaller of two values, or, given a source, its smallest item. Values must be orderable (`deriving ord` for a tuple or enum you declare).

**Parameters**

- `a`, `b`: two values of one type; or
- `xs`: a source of items.

**Returns** the smaller value; for a source, `Ok(item)`, or `Err` (code `MISSING`) when it is empty.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> min(3, 5)
3
```

```
> min("b", "a")
"a"
```

```
> List(3, 1, 2) |> min()
Ok(1)
```

```
> List() |> min()
Err(Error(code: 4, message: "empty"))
```

