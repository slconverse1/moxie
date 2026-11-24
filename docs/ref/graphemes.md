---
layout: default
toc: true
terms: true
title: "graphemes · moxie function"
---

# `graphemes`

<p class="specref"><a href="../reference.html#fn-graphemes">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn graphemes(s String) Stream[String]
```

## Description {#description}

The characters of a `String` as a reader sees them, each as a small `String`. An accented letter, or an emoji built from several code points, is one grapheme.

**Parameters**

- `s`: a `String`.

**Returns** a `Stream[String]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> "abc" |> graphemes() |> collect()
List("a", "b", "c")
```

