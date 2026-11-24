---
layout: default
toc: true
terms: true
dialect: gc
title: "collect_errors · moxie/gc function"
---

# `collect_errors`

<p class="specref"><a href="../reference.html#fn-collect_errors">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn collect_errors[T, E](rs Seq[Result[T, E]]) Result[List[T], List[E]]
```

## Description {#description}

Gathers a list of `Result`s into one: all the values if every item is `Ok`, otherwise all the errors, not just the first.

**Parameters**

- `rs`: the `Result`s.

**Returns** `Ok(values)` or `Err(errors)`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> collect_errors(List(Ok(1), Ok(2)))
Ok(List(1, 2))
```

```
> collect_errors(List(Ok(1), Err("a"), Err("b")))
Err(List("a", "b"))
```

