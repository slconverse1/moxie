---
layout: default
toc: true
terms: true
dialect: gc
title: "all · moxie/gc function"
---

# `all`

<p class="specref"><a href="../reference.html#fn-all">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn all[T](f (T) -> Bool, xs Seq[T]) Bool
```

## Description {#description}

True if the test holds for every item. It stops at the first item that fails. An empty source gives true.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> all((x) -> x > 0)
true
```

```
> List() |> all((x) -> x > 2)
true
```

