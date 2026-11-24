---
layout: default
toc: true
terms: true
dialect: gc
title: "indices · moxie/gc function"
---

# `indices`

<p class="specref"><a href="../reference.html#fn-indices">The alphabetical list</a> · <a href="../spec.html#s7">Spec §7</a></p>

## Signature {#signature}

```
fn indices[T](xs Seq[T]) Range
fn indices(s String) Range
```

## Description {#description}

The positions of a list, array or string, from 0 up to one less than its length. For a `String` the positions are byte positions.

**Parameters**

- `xs`: a collection or a `String`.

**Returns** a `Range`, such as `0..<3`, which can be used in a `for`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> indices(List(5, 6, 7))
0..<3
```

```
> indices("abc")
0..<3
```

