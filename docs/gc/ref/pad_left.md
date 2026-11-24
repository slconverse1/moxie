---
layout: default
toc: true
terms: true
dialect: gc
title: "pad_left · moxie/gc function"
---

# `pad_left`

<p class="specref"><a href="../reference.html#fn-pad_left">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn pad_left(s String, n Int) String
fn pad_left(s String, n Int, c String) String
fn pad_left(s String, n Int, c Char) String
```

## Description {#description}

Adds fill on the left until the text is `n` characters long (right-aligning it). Text that is already long enough is left alone; nothing is cut. The fill defaults to a space.

**Parameters**

- `s`: the text.
- `n`: the width to reach.
- `c` (optional): the fill, a `String` or `Char`.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> pad_left("7", 3)
"  7"
```

```
> pad_left("7", 3, "0")
"007"
```

```
> pad_left("7", 3, '0')
"007"
```

```
> pad_left("abcd", 3)
"abcd"
```

