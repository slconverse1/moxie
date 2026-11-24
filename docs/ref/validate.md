---
layout: default
toc: true
terms: true
title: "validate · moxie function"
---

# `validate`

<p class="specref"><a href="../reference.html#fn-validate">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn validate[T, U](f (T) -> Result[U, Error], xs Seq[T]) Result[List[U], List[Error]]
```

## Description {#description}

Like `traverse`, but it does not stop at the first failure: every item is tried and every error is reported. It suits checking a form, where you want to show all the mistakes at once.

**Parameters**

- `f`: a function from an item to a `Result`.
- `xs`: the items.

**Returns** `Ok(list)` if all succeed, otherwise `Err(list of every error)`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> validate((x) -> if x > 0 then Ok(x) else fail[Int](6, "bad"), List(1, 2))
Ok(List(1, 2))
```

```
> validate((x) -> if x > 0 then Ok(x) else fail[Int](6, "bad"), List(0, 2, -1)) |> map_err((es) -> len(es))
Err(2)
```

