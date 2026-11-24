---
layout: default
toc: true
terms: true
dialect: gc
title: "identity · moxie/gc function"
---

# `identity`

<p class="specref"><a href="../reference.html#fn-identity">The alphabetical list</a> · <a href="../spec.html#s23">Spec §23</a></p>

## Signature {#signature}

```
fn identity[T](x T) T
```

## Description {#description}

Returns its argument unchanged. It is the "do nothing" function, handy as a default where a function is expected.

**Parameters**

- `x`: any value.

**Returns** `x`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> identity(5)
5
```

```
> List(1, 2) |> map(identity) |> collect()
List(1, 2)
```

