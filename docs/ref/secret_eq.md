---
layout: default
toc: true
terms: true
title: "secret_eq · moxie function"
---

# `secret_eq`

<p class="specref"><a href="../reference.html#fn-secret_eq">The alphabetical list</a> · <a href="../spec.html#s23">Spec §23</a></p>

## Signature {#signature}

```
fn secret_eq[T](a Secret[T], b Secret[T]) Bool
```

## Description {#description}

Compares two `Secret` values in constant time, so the time taken doesn't reveal how much of them matched. It is the only way to compare secrets; `==` on a `Secret` is not allowed. The contents are never shown.

**Parameters**

- `a`, `b`: two `Secret`s of one type.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> secret_eq(token_a, token_b)
true or false, in time that does not depend on the contents
```

