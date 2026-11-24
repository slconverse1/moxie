---
layout: default
toc: true
terms: true
dialect: gc
title: "par_traverse · moxie/gc function"
---

# `par_traverse`

<p class="specref"><a href="../reference.html#fn-par_traverse">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn par_traverse[T, U, E](f (T) -> Result[U, E], xs Seq[T], limit: Int) Result[List[U], E]
```

## Description {#description}

Like `par_map`, but for a function that can fail. If a call fails, the others are cancelled and you get that error.

**Parameters**

- `f`: a function from an item to a `Result`.
- `xs`: the items.
- `limit:`: how many calls may run at once.

**Returns** `Ok(list of values)` in order, or the first `Err`.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> par_traverse((x) -> Ok(x + 1), List(1, 2, 3), limit: 2)
Ok(List(2, 3, 4))
```

