---
layout: default
toc: true
terms: true
title: "replace_text · moxie function"
---

# `replace_text`

<p class="specref"><a href="../reference.html#fn-replace_text">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn replace_text(s String, from String, to String) String
```

## Description {#description}

Replaces every occurrence of one piece of text with another. It is for text; for changing a part of a data value, see `replace`.

**Parameters**

- `s`: the text.
- `from`: what to look for.
- `to`: what to put in its place.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> replace_text("a-b-c", "-", "+")
"a+b+c"
```

```
> replace_text("aaa", "a", "bb")
"bbbbbb"
```

