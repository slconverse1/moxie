---
layout: default
toc: true
terms: true
dialect: gc
title: "eprintln · moxie/gc function"
---

# `eprintln`

<p class="specref"><a href="../reference.html#fn-eprintln">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn eprintln() Unit
fn eprintln[T](x T) Unit
fn eprintln[T](out Io, x T) Unit
```

## Description {#description}

Like `println`, but to the error stream, which is where messages for the person running the program, as opposed to the program's output, belong.

**Parameters**

- `out` (optional): an `Io`.
- `x` (optional): the value.

**Returns** nothing.

## Effects {#effects}

**Effect:** prints

## Examples {#examples}

```
> eprintln("something went wrong")
(written to the error stream)
```

