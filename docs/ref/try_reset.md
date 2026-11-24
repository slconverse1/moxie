---
layout: default
toc: true
terms: true
title: "try_reset · moxie function"
---

# `try_reset`

<p class="specref"><a href="../reference.html#fn-try_reset">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn try_reset[T](a Atom[T], v T) Result[T, Error]
```

## Description {#description}

Like `reset`, but if the atom's validator rejects the new value you get an `Err` instead of an abort, and the atom is unchanged.

**Parameters**

- `a`: the `Atom`.
- `v`: the new value.

**Returns** `Ok(new value)`, or `Err` with code `OUT_OF_RANGE`.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> a = Atom(1)
println(try_reset(a, 9))
Ok(9)
```

