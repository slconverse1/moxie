---
layout: default
toc: true
terms: true
dialect: gc
title: "gen_bool · moxie/gc function"
---

# `gen_bool`

<p class="specref"><a href="../reference.html#fn-gen_bool">The alphabetical list</a> · <a href="../spec.html#s22">Spec §22</a></p>

## Signature {#signature}

```
fn gen_bool(g Gen) Bool
```

## Description {#description}

A random `true` or `false` for a property test.

**Parameters**

- `g`: the `Gen`.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> gen_bool(g)
true
```

