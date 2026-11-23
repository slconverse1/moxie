---
layout: default
learn: true
title: "Values and names · Moxie Mixer’s Guide"
---
# 3. Values and names

<div class='specref' markdown='1'>In the Spec: [0. Principles](../spec.html#s0), [1. Source, blocks, bindings](../spec.html#s1), [2. Names and keywords](../spec.html#s2), [3. Memory model: S-space, T-space, and resets](../spec.html#s3)</div>

A moxie program is mostly *values* and the *names* you give them. This lesson covers the building blocks: how to bind a name, what kinds of value there are, and the one rule about names that surprises people coming from other languages.

## Binding a name

`name = value` binds a name to a value. After that, the name stands for the value:

```moxie
width = 4
height = 5
area = width * height
println("area is $area")
```
**Output:**

```
area is 20
```

There is no keyword like `let` or `var`: a line that starts with a new name and `=` is a binding. Names start with a lowercase letter or an underscore, and continue with letters, digits, and underscores: `width`, `total_2`, `_scratch`. Type names, such as `Int` and `String`, start with a capital letter. The convention is `snake_case` for values and functions and `CamelCase` for types.

## Every value has a type

Each value has a *type*, and the compiler works out the type from the value. You rarely write it:

```moxie
count = 3
price = 9.5
label = "apples"
ready = true
initial = 'A'
println("$count $price $label $ready $initial")
```
**Output:**

```
3 9.5 apples true A
```

Here `count` is an `Int` (a whole number), `price` is a `Double` (a number with a fraction), `label` is a `String` (text), `ready` is a `Bool` (`true` or `false`), and `initial` is a `Char` (one character, in single quotes). A double-quoted `"A"` is a `String` of one character and a single-quoted `'A'` is a `Char`; they are different types and don't mix.

You can write the type if you want to, after the name:

```moxie
count Int = 3
price Double = 9.5
println("$count $price")
```
**Output:**

```
3 9.5
```

The type comes before the `=` and has no colon: moxie declarations never use colons. Writing the type is how you ask for a particular one (a small integer type, say) and how you document a binding whose type isn't obvious. When the type is written, the compiler checks the value against it:

```moxie
count Int = "three"
```
**The compiler says:**

```
error: mismatched types: expected `Int`, found `String`
```

## Names are fixed to their values

Values never change in moxie. There is no way to reach into `count` and alter it. What you can do is bind the name again, to a new value:

```moxie
x = 5
x = x + 1
println(x)
```
**Output:**

```
6
```

`x = x + 1` doesn't mutate anything: it makes a new binding of `x` whose value is computed from the old one. Because this is so common, there are short forms: `x += 1` means `x = x + 1`, and likewise `-=`, `*=`, `/=`, and `%=`. `x++` and `x--` add and subtract one:

```moxie
count = 10
count += 5
count -= 3
count *= 2
count += 1
println(count)
```
**Output:**

```
25
```

At the top level of a program, and inside any block, a name can be bound again like this. A binding in a *deeper* block, such as the inside of an `if`, hides the name only within that block. This is the rule that surprises people:

```moxie
n = 1
if true
  n = 2
  println("inside: $n")
println("outside: $n")
```
**Output:**

```
inside: 2
outside: 1
```

The inner `n = 2` made a new `n` that exists only inside the `if`. The outer `n` is untouched, and the compiler warns you that the name is hidden. The lesson on loops shows how to update an outer name on purpose (`n@1 = 2`, or a loop's own result), and the lesson on functions explains why a function sees only the names bound above it.

## Several names at once

A binding can take several names on the left, matching several values on the right. This is a *tuple* binding. It is also how you swap two values, with no temporary:

```moxie
a, b = 1, 2
println("$a $b")
a, b = b, a
println("$a $b")
```
**Output:**

```
1 2
2 1
```

The right-hand side is worked out completely before either name is rebound, which is why the swap works. Tuples have their own lesson.

## Ignoring a value

A lone underscore `_` is a name that is never bound. Use it where a value must be accepted but isn't wanted:

```moxie
first, _ = 10, 20
println(first)
```
**Output:**

```
10
```

## Everything is an expression

Most things in moxie produce a value, including `if`, `when`, `for`, and a block marked `do`. That is why you will see `label = if ...` and `area = do ...` throughout this course. The next lessons show each one.

---

[← Your first program](02-first-program.html) · [Contents](./) · [Moxie for imperative programmers →](58-for-imperative-programmers.html)
