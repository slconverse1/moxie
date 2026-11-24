---
layout: default
toc: true
terms: true
title: "ok_or · moxie function"
---

# `ok_or`

<p class="specref"><a href="../reference.html#fn-ok_or">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn ok_or[T](o Option[T], err Error) Result[T, Error]
```

## Description {#description}

Turns an `Option` into a `Result`, supplying the error to use if there is no value.

**Parameters**

- `o`: an `Option`.
- `err`: the `Error` for the `None` case.

**Returns** `Ok(value)` for `Some`, `Err(err)` for `None`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> ok_or(Some(1), Error(4, "missing"))
Ok(1)
```

```
> ok_or(None, Error(4, "missing"))
Err(Error(code: 4, message: "missing"))
```

