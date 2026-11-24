---
layout: default
toc: true
terms: true
dialect: gc
title: "random_bytes · moxie/gc function"
---

# `random_bytes`

<p class="specref"><a href="../reference.html#fn-random_bytes">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn random_bytes(n Int) Array[Byte]
```

## Description {#description}

`n` random bytes, for keys, tokens and salts. They come from the system's random source.

**Parameters**

- `n`: how many bytes.

**Returns** an `Array[Byte]` of length `n`.

## Effects {#effects}

**Effect:** uses the system

## Examples {#examples}

```
> len(random_bytes(4))
4
```

