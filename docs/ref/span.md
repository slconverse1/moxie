---
layout: default
toc: true
terms: true
title: "span · moxie function"
---

# `span`

<p class="specref"><a href="../reference.html#fn-span">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn span[T](f (T) -> Bool, xs Seq[T]) (List[T], List[T])
```

## Description {#description}

Splits the items at the first one that fails the test. The first list holds the items before it, and the second holds that item and everything after it, whether or not later items pass.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a pair of lists.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> span((x) -> x < 3)
(List(1, 2), List(3, 4))
```

