---
layout: default
toc: true
terms: true
title: "guard · moxie function"
---

# `guard`

<p class="specref"><a href="../reference.html#fn-guard">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn guard(ok Bool) Result[Unit, Error]
```

## Description {#description}

A shorter `ensure`, with a built-in error, for when the reason is clear from where the check is.

**Parameters**

- `ok`: the condition that must hold.

**Returns** `Ok(())` if it holds, otherwise an `Err` with code `MISSING` and the message "guard".

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> guard(1 < 2)
Ok(())
```

```
> guard(2 < 1)
Err(Error(code: 4, message: "guard"))
```

