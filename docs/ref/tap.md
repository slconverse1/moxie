---
layout: default
toc: true
terms: true
title: "tap · moxie function"
---

# `tap`

<p class="specref"><a href="../reference.html#fn-tap">The alphabetical list</a> · <a href="../spec.html#s23">Spec §23</a></p>

## Signature {#signature}

```
fn tap[T, U](x T, f (T) -> U) T
```

## Description {#description}

Runs a function on a value for its effect, such as printing, and then gives back the original value, so it can sit in the middle of a `|>` chain.

**Parameters**

- `x`: the value.
- `f`: the function to call with it; its result is ignored.

**Returns** `x`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> tap(5, (x) -> x * 100)
5
```

