---
layout: default
toc: true
terms: true
dialect: gc
title: "eprint · moxie/gc function"
---

# `eprint`

<p class="specref"><a href="../reference.html#fn-eprint">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn eprint[T](x T) Unit
fn eprint[T](out Io, x T) Unit
```

## Description {#description}

Like `print`, but to the error stream.

**Parameters**

- `out` (optional): an `Io`.
- `x`: the value.

**Returns** nothing.

## Effects {#effects}

**Effect:** prints

## Examples {#examples}

```
> eprint("working...")
(written to the error stream)
```

