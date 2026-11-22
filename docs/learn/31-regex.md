---
layout: default
learn: true
title: "Regular expressions · Learner’s Guide moxie"
---
<p><small>Data from outside</small></p>

# 40. Regular expressions

A regular expression describes the shape of some text. The standard `regex` package is written in moxie, and it runs in time proportional to the text: it never backtracks, so no pattern can hang your program. The price is two missing features, back-references (`\1`) and look-around, and the package says so if you write one.

## The syntax

The syntax is the usual one:

| Written | Meaning |
|---|---|
| `abc` | those characters |
| `.` | any character |
| `[a-z]`, `[^a-z]` | one of a set, or none of it |
| `\d \w \s` (`\D \W \S`) | digit, word character, space (and their opposites) |
| `\b` | a word boundary |
| `^` `$` | the start and end of the text |
| `a\|b` | either |
| `( )`, `(?: )`, `(?<name> )` | a group, a group that only groups, a named capture |
| `* + ? {n} {n,} {n,m}` | repeats |
| `*?` `+?` | lazy repeats |

Inside a moxie string, write each backslash twice, because a string has escapes of its own: `"\\d+"`.

## Patterns in `when`

The most useful place for a regex is a `when`. Write the regex as a string literal, then the names after it, and the compiler reads the regex and gives each name the type its group declares:

- a plain group `( ... )` gives a `String`;
- `(?<n:Int>...)`, `(?<x:Float>...)`, `(?<ok:Bool>...)` give the text already read as that type;
- a group that may not take part (`(...)?`, or one side of a `|`) gives an `Option`.

`Matches` tests the whole text; `Finds` looks for the first match anywhere. They are imported by their bare names, and a `when` that uses one needs a `_` arm.

```moxie
import regex(Matches, Finds)

fn describe(line String) String
  when line
    Matches("(?<y:Int>\\d{4})-(?<m:Int>\\d\\d)-(?<d:Int>\\d\\d)", (y, m, d)) -> "date ${y + 1}/${m}/${d}"
    Finds("(\\w+)@(\\w+)\\.com", (user, host)) -> "mail ${user} at ${host}"
    Matches("v(?<n:Int>\\d+)(?<tag>-[a-z]+)?", (n, tag)) -> "version ${n} ${tag}"
    _ -> "something else"

println(describe("2026-11-20"))
println(describe("write bob@example.com today"))
println(describe("v12-beta"))
println(describe("v7"))
println(describe("2026-11-20 and more"))
```
**Output:**

```
date 2027/11/20
mail bob at example
version 12 Some("-beta")
version 7 None
something else
```

In the first arm `y + 1` is plain arithmetic, because `y` is an `Int`, not text. It is a compile error to write the wrong number of names, to use a name as the wrong type, or to write a regex that doesn't parse, so a mistake doesn't wait for a bad input to show itself.

A regex with no groups takes no names:

```moxie
import regex(Matches)

fn shout(s String) String
  when s
    Matches("ab+") -> "a then b's"
    _ -> "no"

println(shout("abbb"))
println(shout("xab"))
```
**Output:**

```
a then b's
no
```

A regex that doesn't parse is caught at compile time:

```moxie
import regex(Matches)

fn f(s String) String
  when s
    Matches("(ab", (x)) -> x
    _ -> "no"

println(f("ab"))
```
**The compiler says:**

```
error: regex: missing `)` at position 3
```

## Regexes built while the program runs

The compiler can only read a regex that is a string literal. For one you build at run time, compile it once and pin it with `^`. The captures then arrive as a list of `Cap` cases (`CText`, `CInt`, `CFloat`, `CBool`, and `CNone` for a group that didn't take part).

`compile(source)` gives a `Result` whose `Err` says where the pattern went wrong; `must(source)` stops the program on a bad pattern, so use it for a pattern you wrote yourself.

```moxie
import regex(Matches, CInt, must)

suffix = "kg"
weight = must("(?<n:Int>\\d+)${suffix}")

fn grams(s String) Int
  when s
    Matches(^weight, List(CInt(n))) -> n * 1000
    _ -> 0

println(grams("12kg"))
println(grams("12lb"))
```
**Output:**

```
12000
0
```

## The functions

Given a `Regex`, the package's functions take it as the first argument:

```moxie
import regex

words = regex.must("\\w+")
println(regex.find_all(words, "to be or not to be").map((m) -> m.text) |> collect())
println(regex.replace_all(regex.must("\\d+"), "a1b22", (m) -> "<${m.text}>"))
println(regex.split(regex.must(",\\s*"), "a, b,c"))
println(regex.is_match(regex.must("^[a-z]+$"), "hello"))
```
**Output:**

```
List("to", "be", "or", "not", "to", "be")
a<1>b<22>
List("a", "b", "c")
true
```

`find(re, text)` gives the first `Match`, with `start`, `end`, `text`, `groups`, and `named("tag")`. `full(re, text)` requires the whole text to match. `find_all`, `replace_all`, and `split` work from left to right with no overlap. Positions count characters, not bytes.

### What the engine refuses, and why it's fast

A pattern that needs backtracking is rejected, with a message that says where:

```moxie
import regex

println(regex.compile("a{3,1}"))
println(regex.compile("(\\d)\\1"))
```
**Output:**

```
Err(Error(code: 1, message: "regex: the repeat's top is below its bottom at position 6"))
Err(Error(code: 1, message: "regex: back-references are not supported: they need backtracking at position 4"))
```

And a pattern that makes a backtracking engine take exponential time answers at once. `(a+)+b` against 300 letters `a` is the classic bad case:

```moxie
import regex

text = (0..<300) |> map((_) -> "a") |> join("")
println(regex.is_match(regex.must("(a+)+b"), text))
```
**Output:**

```
false
```

## What to remember

- Write the regex as a string literal in a `when` with `Matches` or `Finds`; the names get the types the groups declare.
- Double every backslash in the string.
- For a regex built at run time, use `compile` or `must`, and pin it with `^` in a pattern.
- The engine never backtracks: no back-references, no look-around, and no pattern can hang.
- One small difference from Perl and Python: when the repeated part of a group may match nothing (`(a*)*`), a final empty repetition isn't recorded, so the group keeps its last non-empty text.

*In the Spec: [23f. Regular expressions (the `regex` package)](../spec.html#s23f)*

---

[← JSON and data from outside](30-json.html) · [Contents](./) · [Statistics and prediction →](32-statistics.html)
