---
layout: default
toc: true
terms: true
title: "index · moxie function"
---

# `index`

<p class="specref"><a href="../reference.html#fn-index">The alphabetical list</a> · <a href="../spec.html#s23">Spec §23</a></p>

## Signature {#signature}

```
fn index[E](x E) Int
```

## Description {#description}

The position of an enum case in its declaration, counting from 0.

**Parameters**

- `x`: a value of an enum type.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> enum Color
  Red
  Green
  Blue
println(index(Color.Blue))
2
```

