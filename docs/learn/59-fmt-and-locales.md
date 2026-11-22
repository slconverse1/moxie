---
layout: default
title: "Templates and locales · Learning Guide moxie"
---
<p><small>Getting started</small></p>

# 7. Templates and locales

Lesson 6 introduced format specs inside interpolation, `${price:.2f}`. This lesson covers the other ways to put values into text: a template written apart from its values, a template loaded at run time, and numbers and dates written the way a particular place writes them.

## A template with `fmt`

A template that is written apart from its values uses `fmt`. Each `{}` or `{:spec}` takes the next argument and uses the same specs as interpolation, and `{{` and `}}` are literal braces:

```moxie
price = 12.5
name = "Ann"
println(fmt("{:>8.2f} | {:<5}|", price, name))
println(fmt("{{braces}} {}", 7))
```
**Output:**

```
   12.50 | Ann  |
{braces} 7
```

The template must be a string literal, so the compiler can check the number of fields and each spec against the arguments, and a mismatch is a compile error:

```moxie
println(fmt("{} and {}", 1))
```
**The compiler says:**

```
error: this `fmt` template has 2 fields, but 1 argument is given
```

Prefer interpolation when the text and the values sit together. Use `fmt` when the template is a constant of its own, such as a report line used in many places.

## A template that comes from data

For a template that comes from data, such as a message loaded from a file, use `try_fmt`, which takes any template and returns a `Result`: `Err` with the code `BAD_FORMAT` when the template or the arguments don't fit:

```moxie
template = "{:>6}|{:.1f}"
println(try_fmt(template, "ab", 3.14159))
println(try_fmt(template, "ab"))
```
**Output:**

```
Ok("    ab|3.1")
Err(Error(code: 13, message: "the template has more fields than arguments"))
```

## Locales

The format type `n` writes a number the way a place writes it, using the `Locale` that `using` finds in scope (lesson 10's `using` parameters, here as a top-level declaration):

```moxie
using locale = Locale.de_de
println("${1234567.891:.2n}")
```
**Output:**

```
1.234.567,89
```

Without a `Locale` in scope, `n` is a compile error. `parse_number(text, locale)` reads numbers back and returns a `Result`:

```moxie
using locale = Locale.de_de
println(parse_number("1.234,5", locale))
println(parse_number("oops", locale))
```
**Output:**

```
Ok(1234.5)
Err(Error(code: 4, message: "not a number"))
```

### Dates

The same `Locale` names the days and months when you format a date. With `de_de`, `format_time(t, "%A, %d. %B %Y")` gives the German names, and `%x` writes the date in the locale's order. Pass a `Locale` as a third argument to override the one in scope. `parse_time` reads the same names:

```moxie
using locale = Locale.de_de
t = 1793836800s
d = to_utc(t)
println(format_time(d, "%A, %d. %B %Y"))
println(format_time(d, "%x"))
println(format_time(d, "%x", Locale.fr_fr))
```
**Output:**

```
Donnerstag, 05. November 2026
05.11.2026
05/11/2026
```

## What to remember

- `fmt("{:>8.2f}", x)` checks its template at compile time; `try_fmt` takes any template and returns a `Result`.
- The `n` format type and the names in dates come from the `Locale` found by `using`.
- `parse_number(text, locale)` and `parse_time` read what a locale writes.

---

[← Text](05-text.html) · [Contents](./) · [Truth and choices →](06-truth-and-choices.html)
