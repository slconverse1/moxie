---
layout: default
toc: true
terms: true
title: "first · moxie function"
---

# `first`

<p class="specref"><a href="../reference.html#fn-first">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn first[T](xs Seq[T]) Result[T, Error]
```

## Description {#description}

The first item of a source.

**Parameters**

- `xs`: the items.

**Returns** `Ok(item)`, or `Err` (code `MISSING`, message "empty") if there are none.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(7, 8, 9) |> first()
Ok(7)
```

```
> List() |> first()
Err(Error(code: 4, message: "empty"))
```

