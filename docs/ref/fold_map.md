---
layout: default
toc: true
terms: true
title: "fold_map · moxie function"
---

# `fold_map`

<p class="specref"><a href="../reference.html#fn-fold_map">The alphabetical list</a> · <a href="../spec.html#s23">Spec §23</a></p>

## Signature {#signature}

```
fn fold_map[T, M Monoid](f (T) -> M, xs Seq[T]) M
```

## Description {#description}

Turns each item into a `Monoid` value and combines the results. It is `map` followed by `fold_all` in one step.

**Parameters**

- `f`: a function from an item to a `Monoid` value.
- `xs`: the items.

**Returns** the combined value.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> fold_map((x) -> Sum(x * x), List(1, 2, 3))
Sum(value: 14)
```

```
> fold_map((x) -> show(x), List(1, 2, 3))
"123"
```

