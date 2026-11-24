---
layout: default
toc: true
terms: true
dialect: gc
title: "sequence · moxie/gc function"
---

# `sequence`

<p class="specref"><a href="../reference.html#fn-sequence">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn sequence[T, E](rs Seq[Result[T, E]]) Result[List[T], E]
```

## Description {#description}

Turns a list of `Result`s into one `Result` of a list: all the values if every item is `Ok`, otherwise the first error.

**Parameters**

- `rs`: the `Result`s.

**Returns** `Ok(list)` or the first `Err`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> sequence(List(Ok(1), Ok(2)))
Ok(List(1, 2))
```

```
> sequence(List(Ok(1), Err(Error(1, "x")), Ok(3)))
Err(Error(code: 1, message: "x"))
```

