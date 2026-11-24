---
layout: default
toc: true
terms: true
title: "grapheme_count · moxie function"
---

# `grapheme_count`

<p class="specref"><a href="../reference.html#fn-grapheme_count">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn grapheme_count(s String) Int
```

## Description {#description}

How many characters a reader would count in a `String`, so an accented letter or emoji counts once however it is encoded.

**Parameters**

- `s`: a `String`.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> grapheme_count("abc")
3
```

