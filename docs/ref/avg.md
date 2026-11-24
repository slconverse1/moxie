---
layout: default
toc: true
terms: true
title: "avg · moxie function"
---

# `avg`

<p class="specref"><a href="../reference.html#fn-avg">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn avg(xs Seq[Int]) Result[Float, Error]
fn avg(xs Seq[Float]) Result[Float, Error]
fn avg(xs Seq[Decimal]) Result[Float, Error]
```

## Description {#description}

The mean of the items, as a floating-point number. An empty source has no mean, so it gives an `Err` with the code `MISSING` and the message "empty".

**Parameters**

- `xs`: numbers: `Int`, `Float` or `Decimal` items.

**Returns** `Ok(mean)`, or `Err` for an empty source.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3, 4) |> avg()
Ok(2.5)
```

```
> List() |> avg()
Err(Error(code: 4, message: "empty"))
```

