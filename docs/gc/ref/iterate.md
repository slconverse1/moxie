---
layout: default
toc: true
terms: true
dialect: gc
title: "iterate · moxie/gc function"
---

# `iterate`

<p class="specref"><a href="../reference.html#fn-iterate">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn iterate[T](seed T, f (T) -> T) Stream[T]
```

## Description {#description}

A seed, then `f` of the seed, then `f` of that, and so on, forever. Cut it with `take` or `take_while`.

**Parameters**

- `seed`: the first value.
- `f`: a function from one value to the next.

**Returns** an endless `Stream[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> iterate(1, (x) -> x * 2) |> take(6) |> collect()
List(1, 2, 4, 8, 16, 32)
```

