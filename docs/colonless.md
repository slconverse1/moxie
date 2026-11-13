---
layout: default
title: "Moxie Syntax Changes"
---
# MOXIE WITHOUT THE COLON

Moxie used to put a colon at the end of every header that opened a block, and between every declared name and its type. Both are gone. Indentation already says where a block is, and a name followed by its type already says it is a declaration, so the colon was noise.

This page lists what changed, what did not, and why. The old syntax lives on in the `oldmain` branch of the repository.

## What changed

| Before | Now | |
|---|---|---|
| `if x > 0:` | `if x > 0` | a header opens a block by itself; the block is the indented lines below |
| `if c: a else: b` | `if c then a else b` | one-line `if`; an `else` stays on the same line |
| `for x in xs: f(x)` | `for x in xs do f(x)` | one-line loops use `do` |
| `fn f(x: Int) Int: x + 1` | `fn f(x Int) Int = x + 1` | a one-line function body follows `=` |
| `(x): x + 1` | `(x) -> x + 1` | a lambda |
| `else: ...` in a `when` | `else ...` | the default arm takes no arrow |
| `name: String` in a `tuple` | `name String` | a field |
| `fn f(x: Int, y: String)` | `fn f(x Int, y String)` | a parameter, with `ref n Int`, `lazy x Int`, `xs ...Int` |
| `Circle(r: Float)` in an `enum` | `Circle(r Float)` | a case field |
| `[T: Ord]` | `[T Ord]` | a bound |
| `(x: Int, y: Int)` as a type | `(x Int, y Int)` | a tuple type; function types too |
| `total: Int = 0` | `total Int = 0` | a binding is a declaration |
| `Dict("a": 1)` | `Dict("a" -> 1)` | an entry maps a key to a value; also in patterns, `show`, and `read` |
| `(0: 40)` | `(%40)` | the one-item positional tuple, so it is not mistaken for `(40)` |

Two forms use a bare name as a shorthand (a *pun*):

* After a named argument, a bare name stands for the argument of that name: `User(name: who, age)` is `User(name: who, age: age)`. A bare name before any named argument is positional, as always, so `User(name, age)` passes two values in order.
* In a `Dict`, a bare name stands for the entry whose key is that word and whose value is the variable: `Dict(age, n)` is `Dict(age -> age, n -> n)`.

## What did not change

A value still takes a colon after its name:

* named arguments: `User(name: "Al", age: 3)`
* tuple literals: `(x: 1, y: 2)`
* `update` lines: `port: 443`
* labels in patterns: `Point(x: px)`

The colon also stays in format specs (`${x:>5}`), loop labels, `sql(c): text`, and the REPL commands (`:type`, `:help`).

The result is the same split Go has: `Name string` in a declaration, `Name: "Al"` in a literal. A type follows the name in a declaration, and a value follows the colon in a literal.

## Mistakes are errors, not guesses

The old forms are syntax errors that say what to write: a block header with a colon says to delete it, a declaration with a colon says to write the name and then its type, and a `Dict` entry with a colon names the arrow. There is no period in which both forms work.

## Moving old code

Two scripts in `tools/` convert old source. Run them in this order, and run each **once** on any given file:

1. `python3 tools/colonless.py FILE...` removes block colons and rewrites the one-line forms.
2. `python3 tools/declcolon.py FILE...` removes declaration colons, turns `Dict` colons into arrows, and removes the colon from typed bindings.

Both take `.mxi` files, Python files (they convert the Moxie in string literals), and Markdown files (they convert the code blocks and code spans). The second script asks the parser which colons are declaration colons, so it is exact on code that parses and reports a block it could not read.
