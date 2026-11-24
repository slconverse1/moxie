---
layout: default
toc: true
terms: true
dialect: gc
title: "max · moxie/gc function"
---

# `max`

<p class="specref"><a href="../reference.html#fn-max">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn max[T Ordered](a T, b T) T
fn max[T Ordered](xs Seq[T]) Result[T, Error]
```

## Description {#description}

The larger of two values, or, given a source, its largest item. Values must be orderable (`deriving ord` for a tuple or enum you declare).

**Parameters**

- `a`, `b`: two values of one type; or
- `xs`: a source of items.

**Returns** the larger value; for a source, `Ok(item)`, or `Err` (code `MISSING`) when it is empty.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> max(3, 5)
5
```

```
> max("a", "b")
"b"
```

```
> List(3, 1, 2) |> max()
Ok(3)
```

```
> List() |> max()
Err(Error(code: 4, message: "empty"))
```

