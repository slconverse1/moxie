---
layout: default
toc: true
terms: true
title: "cycle · moxie function"
---

# `cycle`

<p class="specref"><a href="../reference.html#fn-cycle">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn cycle[T](xs Seq[T]) Stream[T]
```

## Description {#description}

Repeats a source forever: after the last item it starts again at the first. The stream never ends, so cut it with `take`, `take_while` or a `break`. An empty source gives an empty stream.

**Parameters**

- `xs`: the items to repeat.

**Returns** an endless `Stream[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> cycle() |> take(7) |> collect()
List(1, 2, 3, 1, 2, 3, 1)
```

