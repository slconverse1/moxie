---
layout: default
toc: true
terms: true
dialect: gc
title: "partition_results · moxie/gc function"
---

# `partition_results`

<p class="specref"><a href="../reference.html#fn-partition_results">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn partition_results[T, E](rs Seq[Result[T, E]]) (List[T], List[E])
```

## Description {#description}

Splits a list of `Result`s into the values and the errors, keeping the order. Nothing is lost and nothing fails; use it to keep going with what worked and report what did not.

**Parameters**

- `rs`: the `Result`s.

**Returns** a pair `(values, errors)`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> partition_results(List(Ok(1), Err("a"), Ok(2)))
(List(1, 2), List("a"))
```

