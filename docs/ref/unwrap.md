---
layout: default
toc: true
terms: true
title: "unwrap · moxie function"
---

# `unwrap`

<p class="specref"><a href="../reference.html#fn-unwrap">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn unwrap[T, E](r Result[T, E]) T
```

## Description {#description}

The value inside an `Ok`. An `Err` aborts the program, so use it only where an error would mean a bug, for instance on a literal you know is valid. Everywhere else, handle the `Err`, or pass it on with `?`.

**Parameters**

- `r`: a `Result`.

**Returns** the value.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> unwrap(Ok(5))
5
```

```
> unwrap(Err(Error(4, "missing")))
aborts the program with the error
```

