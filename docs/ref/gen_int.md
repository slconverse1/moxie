---
layout: default
toc: true
terms: true
title: "gen_int · moxie function"
---

# `gen_int`

<p class="specref"><a href="../reference.html#fn-gen_int">The alphabetical list</a> · <a href="../spec.html#s22">Spec §22</a></p>

## Signature {#signature}

```
fn gen_int[T](g Gen, lo T, hi T) T
```

## Description {#description}

A random whole number between two bounds, both included, for a property test. The generator `g` is handed to the test by `moxie test`, which prints the seed when a test fails, so the failure can be replayed.

**Parameters**

- `g`: the `Gen`.
- `lo`, `hi`: the bounds.

**Returns** an integer in the range.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> gen_int(g, 0, 100)
37  (a different number each run, same for a given seed)
```

