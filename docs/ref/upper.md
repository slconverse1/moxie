---
layout: default
toc: true
terms: true
title: "upper · moxie function"
---

# `upper`

<p class="specref"><a href="../reference.html#fn-upper">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn upper(s String) String
fn upper(c Char) Char
```

## Description {#description}

Converts text to upper case. Given a `String`, every letter is converted; given a `Char`, just that character.

**Parameters**

- `s`: a `String` or a `Char`.

**Returns** the same type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> upper("Hello")
"HELLO"
```

```
> upper('a')
"A"
```

