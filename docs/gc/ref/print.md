---
layout: default
toc: true
terms: true
dialect: gc
title: "print · moxie/gc function"
---

# `print`

<p class="specref"><a href="../reference.html#fn-print">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn print[T](x T) Unit
fn print[T](out Io, x T) Unit
```

## Description {#description}

Like `println`, but without the line end, so the next output continues on the same line. Output may be held back until a line end or until `flush`.

**Parameters**

- `out` (optional): an `Io` to write to.
- `x`: the value.

**Returns** nothing.

## Effects {#effects}

**Effect:** prints

## Examples {#examples}

```
> print("a")
print("b")
println()
ab
```

