---
layout: default
toc: true
terms: true
dialect: gc
title: "starts_with · moxie/gc function"
---

# `starts_with`

<p class="specref"><a href="../reference.html#fn-starts_with">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn starts_with(s String, prefix String) Bool
fn starts_with(s String, c Char) Bool
```

## Description {#description}

True if a `String` begins with a prefix.

**Parameters**

- `s`: the text.
- `prefix`: a `String` or a `Char`.

**Returns** a `Bool`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> starts_with("hello", "he")
true
```

```
> starts_with("hello", 'x')
false
```

