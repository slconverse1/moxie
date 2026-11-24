---
layout: default
toc: true
terms: true
title: "gen_pick · moxie function"
---

# `gen_pick`

<p class="specref"><a href="../reference.html#fn-gen_pick">The alphabetical list</a> · <a href="../spec.html#s22">Spec §22</a></p>

## Signature {#signature}

```
fn gen_pick[T](g Gen, xs List[T]) T
```

## Description {#description}

A random item of a list, for a property test.

**Parameters**

- `g`: the `Gen`.
- `xs`: a non-empty `List`.

**Returns** one of its items.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> gen_pick(g, List("a", "b", "c"))
"b"
```

