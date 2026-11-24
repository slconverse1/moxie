---
layout: default
toc: true
terms: true
title: "assert_eq · moxie function"
---

# `assert_eq`

<p class="specref"><a href="../reference.html#fn-assert_eq">The alphabetical list</a> · <a href="../spec.html#s22">Spec §22</a></p>

## Signature {#signature}

```
fn assert_eq[T](a T, b T) Unit
```

## Description {#description}

Checks that two values are equal and, if they are not, reports both so you can see the difference.

**Parameters**

- `a`, `b`: two values of one type.

**Returns** nothing.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> assert_eq(1 + 1, 2)
println("fine")
fine
```

```
> assert_eq(1 + 1, 3)
aborts, showing 2 and 3
```

