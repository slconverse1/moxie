---
layout: default
toc: true
terms: true
dialect: gc
title: "parse_number · moxie/gc function"
---

# `parse_number`

<p class="specref"><a href="../reference.html#fn-parse_number">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn parse_number[N](s String) Result[N, Error]
fn parse_number[N](s String, locale Locale) Result[N, Error]
```

## Description {#description}

Reads a number from text. Text with a decimal point gives a `Double`, and text without one gives an `Int`. A sign is allowed and so is a leading space; anything else is an error, and nothing aborts. With a `Locale`, the group and decimal marks of that locale are understood, so `"1.234,5"` can be read in German.

**Parameters**

- `s`: the text.
- `locale` (optional): a `Locale` such as `Locale.de_de`.

**Returns** `Ok(number)`, or `Err` (code `MISSING`, message "not a number").

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> parse_number("42")
Ok(42)
```

```
> parse_number("-7")
Ok(-7)
```

```
> parse_number("3.5")
Ok(3.5)
```

```
> parse_number("x")
Err(Error(code: 4, message: "not a number"))
```

```
> parse_number("1e3")
Err(Error(code: 4, message: "not a number"))
```

