---
layout: default
toc: true
terms: true
title: "find · moxie function"
---

# `find`

<p class="specref"><a href="../reference.html#fn-find">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn find[T](f (T) -> Bool, xs Seq[T]) Result[T, Error]
```

## Description {#description}

The first item for which the test is true. If no item passes, the result is an `Err` with the code `MISSING` and the message "not found", so the caller must say what to do about it.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** `Ok(item)` or `Err`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> find((x) -> x > 1)
Ok(2)
```

```
> List(1, 2, 3) |> find((x) -> x > 5)
Err(Error(code: 4, message: "not found"))
```

