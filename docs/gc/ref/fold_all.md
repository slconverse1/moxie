---
layout: default
toc: true
terms: true
dialect: gc
title: "fold_all · moxie/gc function"
---

# `fold_all`

<p class="specref"><a href="../reference.html#fn-fold_all">The alphabetical list</a> · <a href="../spec.html#s23">Spec §23</a></p>

## Signature {#signature}

```
fn fold_all[T Monoid](xs Seq[T]) T
```

## Description {#description}

Combines every item of a source with the type's own `combine`, starting from its `empty`. The item type must be a `Monoid`: a type with an identity and an associative way to combine two values. `String` joins and `List` appends; for numbers, wrap each in `Sum` (or `Product`, `Min`, `Max`), whose `value` field holds the result.

**Parameters**

- `xs`: a source of items of a `Monoid` type.

**Returns** the combined value; `empty` for no items.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> fold_all(List("a", "b", "c"))
"abc"
```

```
> fold_all(List(Sum(1), Sum(2), Sum(3)))
Sum(value: 6)
```

```
> fold_all(List(List(1), List(2, 3)))
List(1, 2, 3)
```

