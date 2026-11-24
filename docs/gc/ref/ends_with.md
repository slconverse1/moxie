---
layout: default
toc: true
terms: true
dialect: gc
title: "ends_with · moxie/gc function"
---

# `ends_with`

<p class="specref"><a href="../reference.html#fn-ends_with">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn ends_with(s String, suffix String) Bool
fn ends_with(s String, c Char) Bool
```

## Description {#description}

True if a `String` ends with a suffix.

**Parameters**

- `s`: the text.
- `suffix`: a `String` or a `Char`.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> ends_with("hello", "llo")
true
```

```
> ends_with("hello", 'x')
false
```

