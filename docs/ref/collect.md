---
layout: default
toc: true
terms: true
title: "collect · moxie function"
---

# `collect`

<p class="specref"><a href="../reference.html#fn-collect">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn collect[T](xs Seq[T]) List[T]
```

## Description {#description}

Gathers a stream into a `List`, which runs the pipeline. A `List`, `Array` or `Set` given to it comes back as a list of its items.

**Parameters**

- `xs`: the source to gather.

**Returns** a `List[T]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> filter((x) -> x > 2) |> collect()
List(3, 4)
```

```
> Set(3) |> collect()
List(3)
```

