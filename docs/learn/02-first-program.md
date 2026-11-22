---
layout: default
title: "Your first program · Learn moxie"
---
<p><small>Getting started</small></p>

# 2. Your first program

A moxie program is a file of statements. The interpreter reads them from the top, in order, and the top of the file you run behaves like the body of a function named `main`: you do not write `main` yourself, and there is no boilerplate. The smallest program is one line:

```moxie
println("Hello, moxie")
```
**Output:**

```
Hello, moxie
```

`println` writes its argument followed by a newline. `print` writes it without one:

```moxie
print("one ")
print("two ")
println("three")
```
**Output:**

```
one two three
```

## Text in quotes

A piece of text is written in double quotes and is called a `String`. A string can hold any characters, including accented letters and emoji:

```moxie
println("naïve café ✓")
```
**Output:**

```
naïve café ✓
```

Inside a string, a backslash starts an escape. `\n` is a newline, `\t` a tab, `\"` a double quote, and `\\` a backslash:

```moxie
println("a\tb\nc \"quoted\" and a backslash: \\")
```
**Output:**

```
a	b
c "quoted" and a backslash: \
```

## Putting values into text

A `$` in a string inserts a value. `$name` inserts the name's value, and `${...}` inserts any expression. This is called *interpolation*, and it is the usual way to print more than one thing:

```moxie
name = "Ada"
year = 1843
println("$name wrote the first program in $year")
println("two plus two is ${2 + 2}")
```
**Output:**

```
Ada wrote the first program in 1843
two plus two is 4
```

To write a literal dollar sign, escape it with a backslash: `"\$5"`.

```moxie
println("it costs \$5")
```
**Output:**

```
it costs $5
```

## Comments

A comment is text the interpreter ignores. `//` starts a comment that runs to the end of the line, and `/* ... */` can span lines:

```moxie
// this line is ignored
println("before") // so is the end of this one
/* a comment
   over two lines */
println("after")
```
**Output:**

```
before
after
```

A comment that starts with three slashes, `///`, documents the declaration that follows it, and a later lesson shows how those become documentation.

## Statements and lines

A moxie statement is one line, and there are no semicolons. A long statement can be split inside parentheses or after an operator; a later lesson shows the rules. Blank lines are free. Indentation, two spaces per level, begins a block, as in `if` and `for`, covered soon.

## When something is wrong

If the interpreter finds a mistake it tells you which line, and the program doesn't run at all:

```moxie
println("hi"
```
**The compiler says:**

```
syntax error: expected ')' to close the argument list
```

The message is the reference interpreter's. Reading it is a skill worth building early: it names the line and column, and says what it expected to find.

---

[← Running moxie](01-run.html) · [Contents](./) · [Values and names →](03-values-and-names.html)
