---
layout: default
toc: true
terms: true
title: "last · moxie function"
---

# `last`

<p class="specref"><a href="../reference.html#fn-last">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn last[T](xs Seq[T]) Result[T, Error]
```

## Description {#description}

The last item of a source. It reads the whole source, so it must be finite.

**Parameters**

- `xs`: the items.

**Returns** `Ok(item)`, or `Err` (code `MISSING`, message "empty") if there are none.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(7, 8, 9) |> last()
Ok(9)
```

```
> List() |> last()
Err(Error(code: 4, message: "empty"))
```

