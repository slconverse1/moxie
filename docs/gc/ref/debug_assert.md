---
layout: default
toc: true
terms: true
dialect: gc
title: "debug_assert · moxie/gc function"
---

# `debug_assert`

<p class="specref"><a href="../reference.html#fn-debug_assert">The alphabetical list</a> · <a href="../spec.html#s22">Spec §22</a></p>

## Signature {#signature}

```
fn debug_assert(ok Bool) Unit
```

## Description {#description}

Like `assert`, but only checked when the program is run in debug mode; in a release build it costs nothing. Use it for checks that are too slow to leave on, and never for checks that guard against bad input.

**Parameters**

- `ok`: the condition that must hold.

**Returns** nothing.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> debug_assert(1 < 2)
println("fine")
fine
```

