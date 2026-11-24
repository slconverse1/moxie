---
layout: default
toc: true
terms: true
title: "ensure · moxie function"
---

# `ensure`

<p class="specref"><a href="../reference.html#fn-ensure">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn ensure[E](ok Bool, e E) Result[Unit, E]
```

## Description {#description}

Checks a condition, and gives a `Result` you can use with `?` to stop early. It is the usual way to write a guard whose failure carries its own error value.

**Parameters**

- `ok`: the condition that must hold.
- `e`: the error to produce if it does not.

**Returns** `Ok(())` if the condition holds, otherwise `Err(e)`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> ensure(1 < 2, "too small")
Ok(())
```

```
> ensure(2 < 1, "too small")
Err("too small")
```

