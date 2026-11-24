---
layout: default
toc: true
terms: true
dialect: gc
title: "lower · moxie/gc function"
---

# `lower`

<p class="specref"><a href="../reference.html#fn-lower">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn lower(s String) String
fn lower(c Char) Char
```

## Description {#description}

Converts text to lower case. Given a `String`, every letter is converted; given a `Char`, just that character.

**Parameters**

- `s`: a `String` or a `Char`.

**Returns** the same type.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> lower("Hello")
"hello"
```

```
> lower('A')
"a"
```

