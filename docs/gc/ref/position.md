---
layout: default
toc: true
terms: true
dialect: gc
title: "position · moxie/gc function"
---

# `position`

<p class="specref"><a href="../reference.html#fn-position">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn position[T](f (T) -> Bool, xs Seq[T]) Result[Int, Error]
```

## Description {#description}

The position, counting from 0, of the first item for which the test is true.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** `Ok(index)`, or `Err` (code `MISSING`, message "not found") if no item passes.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(5, 3, 9) |> position((x) -> x == 9)
Ok(2)
```

```
> List(5, 3, 9) |> position((x) -> x == 1)
Err(Error(code: 4, message: "not found"))
```

