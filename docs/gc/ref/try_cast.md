---
layout: default
toc: true
terms: true
dialect: gc
title: "try_cast · moxie/gc function"
---

# `try_cast`

<p class="specref"><a href="../reference.html#fn-try_cast">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn try_cast[T Numeric, N Numeric](x N) Result[T, Error]
```

## Description {#description}

Like `cast`, but a value that doesn't fit is a `Result` and not an abort.

**Parameters**

- `T` (in brackets): the type to convert to.
- `x`: the number.

**Returns** `Ok(value)`, or `Err` (code `OUT_OF_RANGE`, message "does not fit").

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> try_cast[Int8](100)
Ok(100)
```

```
> try_cast[Int8](300 + len(""))
Err(Error(code: 6, message: "does not fit"))
```

```
> try_cast[UInt8](-1)
Err(Error(code: 6, message: "does not fit"))
```

