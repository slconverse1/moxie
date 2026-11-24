---
layout: default
toc: true
terms: true
dialect: gc
title: "assert · moxie/gc function"
---

# `assert`

<p class="specref"><a href="../reference.html#fn-assert">The alphabetical list</a> · <a href="../spec.html#s22">Spec §22</a></p>

## Signature {#signature}

```
fn assert(ok Bool) Unit
fn assert(ok Bool, message String) Unit
```

## Description {#description}

Stops the program with a message if a condition is false. In a `test`, a failed assertion fails the test and the other tests go on. An optional message says what was expected.

**Parameters**

- `ok`: the condition that must hold.
- `message` (optional): what to report if it doesn't.

**Returns** nothing.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> assert(1 < 2)
println("fine")
fine
```

```
> assert(1 > 2, "one is not bigger")
aborts: assertion failed: one is not bigger
```

