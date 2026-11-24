---
layout: default
toc: true
terms: true
title: "traverse · moxie function"
---

# `traverse`

<p class="specref"><a href="../reference.html#fn-traverse">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn traverse[T, U](f (T) -> Result[U, Error], xs Seq[T]) Result[List[U], Error]
```

## Description {#description}

Applies a function that can fail to every item. If all succeed you get all the results; at the first failure you get that error and no more items are processed.

**Parameters**

- `f`: a function from an item to a `Result`.
- `xs`: the items.

**Returns** `Ok(list)` of the results, or the first `Err`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> traverse((x) -> if x > 0 then Ok(x * 2) else fail[Int](6, "not positive"), List(1, 2, 3))
Ok(List(2, 4, 6))
```

```
> traverse((x) -> if x > 0 then Ok(x * 2) else fail[Int](6, "not positive"), List(1, 0, 3))
Err(Error(code: 6, message: "not positive"))
```

