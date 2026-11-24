---
layout: default
toc: true
terms: true
dialect: gc
title: "repeat · moxie/gc function"
---

# `repeat`

<p class="specref"><a href="../reference.html#fn-repeat">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn repeat[T](x T) Stream[T]
```

## Description {#description}

The same value over and over, forever. Cut it with `take`.

**Parameters**

- `x`: the value to repeat.

**Returns** an endless `Stream[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> repeat("ab") |> take(3) |> collect()
List("ab", "ab", "ab")
```

