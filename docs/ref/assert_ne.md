---
layout: default
toc: true
terms: true
title: "assert_ne · moxie function"
---

# `assert_ne`

<p class="specref"><a href="../reference.html#fn-assert_ne">The alphabetical list</a> · <a href="../spec.html#s22">Spec §22</a></p>

## Signature {#signature}

```
fn assert_ne[T](a T, b T) Unit
```

## Description {#description}

Checks that two values are different.

**Parameters**

- `a`, `b`: two values of one type.

**Returns** nothing.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> assert_ne(1, 2)
println("fine")
fine
```

```
> assert_ne(1, 1)
aborts
```

