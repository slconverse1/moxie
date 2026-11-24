---
layout: default
toc: true
terms: true
title: "join · moxie function"
---

# `join`

<p class="specref"><a href="../reference.html#fn-join">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn join[T](xs Seq[T], sep String) String
fn join[T](xs Seq[T]) String
```

## Description {#description}

Makes one `String` from the items, with `sep` between them. Each item is shown as text first, so numbers and other values can be joined too. Without a separator the items are run together.

**Parameters**

- `xs`: the items.
- `sep` (optional): the text to put between items.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> join(List("a", "b", "c"), ", ")
"a, b, c"
```

```
> join(List(1, 2, 3), "-")
"1-2-3"
```

```
> join(List(1, 2, 3))
"123"
```

