---
layout: default
toc: true
terms: true
title: "unzip · moxie function"
---

# `unzip`

<p class="specref"><a href="../reference.html#fn-unzip">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn unzip[A, B](xs Seq[(A, B)]) (List[A], List[B])
```

## Description {#description}

Splits a source of pairs into two lists: the first parts and the second parts. It is the opposite of `zip`.

**Parameters**

- `xs`: a source of pairs.

**Returns** a pair of lists, `(List[A], List[B])`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> unzip(List((1, "a"), (2, "b")))
(List(1, 2), List("a", "b"))
```

