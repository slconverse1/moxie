---
layout: default
toc: true
terms: true
title: "partition · moxie function"
---

# `partition`

<p class="specref"><a href="../reference.html#fn-partition">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn partition[T](f (T) -> Bool, xs Seq[T]) (List[T], List[T])
```

## Description {#description}

Splits the items into two lists: those for which the test is true, and the rest. Each list keeps the original order.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a pair of lists, `(passed, failed)`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> partition((x) -> x % 2 == 0)
(List(2, 4), List(1, 3))
```

