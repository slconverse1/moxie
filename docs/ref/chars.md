---
layout: default
toc: true
terms: true
title: "chars · moxie function"
---

# `chars`

<p class="specref"><a href="../reference.html#fn-chars">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn chars(s String) Stream[Char]
```

## Description {#description}

The characters of a `String`, one at a time. A `Char` is one Unicode code point, so a letter with a combining accent is two of them; use `graphemes` for what a reader sees as one character.

**Parameters**

- `s`: a `String`.

**Returns** a `Stream[Char]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> "abc" |> chars() |> collect()
List('a', 'b', 'c')
```

