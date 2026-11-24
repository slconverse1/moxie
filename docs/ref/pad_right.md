---
layout: default
toc: true
terms: true
title: "pad_right · moxie function"
---

# `pad_right`

<p class="specref"><a href="../reference.html#fn-pad_right">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn pad_right(s String, n Int) String
fn pad_right(s String, n Int, c String) String
fn pad_right(s String, n Int, c Char) String
```

## Description {#description}

Adds fill on the right until the text is `n` characters long (left-aligning it). Text that is already long enough is left alone. The fill defaults to a space.

**Parameters**

- `s`: the text.
- `n`: the width to reach.
- `c` (optional): the fill, a `String` or `Char`.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> pad_right("7", 3, "0")
"700"
```

```
> pad_right("ab", 4, '.')
"ab.."
```

