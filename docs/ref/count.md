---
layout: default
toc: true
terms: true
title: "count · moxie function"
---

# `count`

<p class="specref"><a href="../reference.html#fn-count">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn count[T](xs Seq[T]) Int
```

## Description {#description}

How many items a source has. It reads the whole source, so it must be finite.

**Parameters**

- `xs`: the items.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List("a", "b", "c") |> filter((s) -> s == "b") |> count()
1
```

