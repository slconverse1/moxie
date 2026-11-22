---
layout: default
title: "Text · Learn moxie"
---
<p><small>Getting started</small></p>

# 6. Text

Text in moxie is a `String`: a sequence of Unicode characters stored as UTF-8. You have already used strings for printing. This lesson covers what else you can do with them.

## Strings and characters

Double quotes make a `String`. Single quotes make a `Char`, which holds exactly one Unicode character:

```moxie
word = "moxie"
letter = 'm'
println("$word starts with $letter")
```
**Output:**

```
moxie starts with m
```

`''` (empty) and `'ab'` (two characters) are errors, because a `Char` is always exactly one. A `Char` is not a number, so `'a' + 1` doesn't compile, and a `String` is not a list of `Char` values that you can index by position. You work with the pieces through functions, shown below.

## Joining strings

`+` joins two strings:

```moxie
first = "Grace"
last = "Hopper"
println(first + " " + last)
```
**Output:**

```
Grace Hopper
```

Interpolation is usually nicer than `+` when several pieces are involved: `"$first $last"` says the same thing. Interpolation also accepts a *format spec* after a colon, which controls how a value is written:

```moxie
price = 12.5
count = 255
name = "Ada"
println("${price:.2f}")
println("${count:08b}")
println("${count:#x}")
println("[${name:>6}]")
println("[${name:<6}]")
println("[${name:^6}]")
println("[${name:*^7}]")
println("${1234567:,}")
```
**Output:**

```
12.50
11111111
0xff
[   Ada]
[Ada   ]
[ Ada  ]
[**Ada**]
1,234,567
```

The spec reads `[[fill]align][sign][#][0][width][,][.precision][type]`. Align is `<` (left), `>` (right) or `^` (center), optionally preceded by a fill character. `.2f` is two digits after the point, `b` is binary, `x` is hexadecimal (with `#`, a `0x` prefix), `0` pads with zeros, and `,` groups thousands. The compiler checks the spec against the type, so `${name:.2f}` on a string is an error.

If you prefer to write the template apart from its values, `fmt` takes `{}` fields:

```moxie
println(fmt("{:>8.2f} | {:<5}|", 12.5, "Ann"))
```
**Output:**

```
   12.50 | Ann  |
```

## Length

`len` counts *bytes*, and `char_count` counts characters. For plain English they agree, and for an accented letter they don't:

```moxie
println(len("hello"))
println(len("héllo"))
println(char_count("héllo"))
```
**Output:**

```
5
6
5
```

A character the eye sees as one thing, such as a flag or a letter with a combining accent, can be several Unicode characters. `grapheme_count` counts what the eye counts:

```moxie
flag = "🇳🇿"
println(char_count(flag))
println(grapheme_count(flag))
```
**Output:**

```
2
1
```

## Slicing

A string slices with parentheses and a range. Offsets are in bytes:

```moxie
s = "Python"
println(s(2..))
println(s(..<3))
println(s(1..3))
println(s(..))
```
**Output:**

```
thon
Pyt
yth
Python
```

A slice is a read-only view of part of the string. A cut in the middle of a multi-byte character aborts, and with constant offsets the compiler catches it. For the usual English text you won't meet that.

## Searching and testing

```moxie
s = "hello, world"
println(contains(s, "lo, w"))
println(starts_with(s, "he"))
println(ends_with(s, "ld"))
println(replace_text(s, "o", "0"))
```
**Output:**

```
true
true
true
hell0, w0rld
```

These can be written either as functions, `contains(s, "x")`, or with a dot, `s.contains("x")`; the dot form just puts the first argument before the name.

## Changing case, trimming, padding

```moxie
println(upper("shout"))
println(lower("QUIET"))
println("  padded  ".trim() + "|")
println(pad_left("7", 3) + "|")
println(pad_right("7", 3) + "|")
```
**Output:**

```
SHOUT
quiet
padded|
  7|
7  |
```

`trim` removes spaces and newlines from both ends. `pad_left` and `pad_right` make a string at least a given width, which lines up columns in a table.

## Splitting and joining

`split` cuts a string at a separator and gives a *stream* of pieces (streams have their own lesson); `collect()` turns the stream into a `List`. `join` goes the other way:

```moxie
words = "a,b,c".split(",").collect()
println(words)
println(words.join("-"))
```
**Output:**

```
List("a", "b", "c")
a-b-c
```

`split_once` cuts at the first separator only, and gives an `Option`: `Some` with both halves, or `None` when the separator isn't there. `strip_prefix` and `strip_suffix` do the same for the ends:

```moxie
println(split_once("key=value=more", "="))
println(split_once("nothing", "="))
println(strip_prefix("v1.2", "v"))
println(strip_suffix("v1.2", ".txt"))
```
**Output:**

```
Some(("key", "value=more"))
None
Some("1.2")
None
```

## Looking at the characters

`chars` is a stream of `Char`s, so you can count, filter, or collect them:

```moxie
println("héllo".chars().collect())
println("banana".chars().filter((c) -> c == 'a').count())
```
**Output:**

```
List('h', 'é', 'l', 'l', 'o')
3
```

## Reading numbers from text

Text that should be a number is turned into one with `read[T]`. Because the text might not be a number, you get a `Result` back, `Ok` with the value or `Err` when it can't be read:

```moxie
println(read[Int]("42"))
println(read[Int]("forty-two"))
println(read[Double]("2.5"))
```
**Output:**

```
Ok(42)
Err(Error(code: 4, message: "cannot read"))
Ok(2.5)
```

The next lessons show how to take a `Result` apart and decide what to do with an `Err`.

## Other ways to write a string

A string can span lines with triple quotes. The opening `"""` ends its line, and the position of the closing `"""` sets the margin that is removed from every line:

```moxie
poem = """
  roses are red
    violets are blue
  """
println(poem)
```
**Output:**

```
roses are red
  violets are blue
```

Quotes inside need no escape, and interpolation still works. A *raw string*, written `r"..."`, has no escapes and no interpolation, which suits file paths and patterns. Add `#` marks to include a quote:

```moxie
path = r"C:\temp\new"
quote = r#"she said "hi""#
println(path)
println(quote)
```
**Output:**

```
C:\temp\new
she said "hi"
```

## Bytes

Byte literals are for protocols and binary data. `b"GET /"` is an `Array[Byte]` of known length, and `b'\x7F'` is one `Byte`. Only ASCII and a few escapes are allowed in them.

```moxie
request = b"GET /"
println(len(request))
```
**Output:**

```
5
```

---

[← Numbers](04-numbers.html) · [Contents](./) · [Templates and locales →](59-fmt-and-locales.html)
