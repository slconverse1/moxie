---
layout: default
toc: true
terms: true
dialect: gc
title: "any · moxie/gc function"
---

# `any`

<p class="specref"><a href="../reference.html#fn-any">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn any[T](f (T) -> Bool, xs Seq[T]) Bool
```

## Description {#description}

True if the test holds for at least one item. It stops at the first item that passes. An empty source gives false.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> any((x) -> x > 2)
true
```

```
> List(1, 2, 3) |> any((x) -> x > 5)
false
```

