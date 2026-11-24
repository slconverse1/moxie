---
layout: default
dialect: gc
learn: true
title: "Truth and choices · Moxie/gc Mixer’s Guide"
---
# 8. Truth and choices

In the Spec: [8. Patterns and `when`](../spec.html#s8), [10. Operators](../spec.html#s10)
{: .specref}

A program becomes interesting when it can decide. This lesson covers `Bool`, comparisons, and the two ways to choose: `if` and `when`.

## Bool

`Bool` has two values, `true` and `false`. Comparisons produce them:

```moxie
age = 20
println(age >= 18)
println(age == 20)
println(age ~= 20)
println(age < 10)
```
**Output:**

```
true
true
false
false
```

The comparison operators are `==`, `~=` (not equal), `<`, `<=`, `>`, and `>=`. There is no `!=`, and `!` is not an operator at all. `=` is a binding and `==` is a test, which is the one place a typo is easy; writing `if x = 5` is an error. Comparisons work on numbers, strings (alphabetical order), characters, and many other types, as long as both sides have the same type:

```moxie
println("apple" < "banana")
println('a' < 'b')
```
**Output:**

```
true
true
```

Comparisons chain, so a range check reads the way you would say it. `0 <= x <= 100` means `0 <= x and x <= 100`, and the middle value is worked out once:

```moxie
x = 42
println(0 <= x <= 100)
println(0 <= x <= 10)
```
**Output:**

```
true
false
```

As with arithmetic, comparing an `Int` variable to a `Double` is rejected, and the fix is a `cast`. A bare literal is fine, because it takes the type of the other side:

```moxie
x = 5
println(x == 5.0)
```
**The compiler says:**

```
error: cannot apply `==` to `Int` and `Double`: an integer this wide does not fit a `Double` exactly, so convert on purpose (`cast[Double](x)`)
```

## and, or, not

Combine `Bool` values with `and`, `or`, and `not`. They are words, not symbols. `and` and `or` stop early: `a and b` doesn't evaluate `b` when `a` is already false.

```moxie
age = 20
member = false
println(age >= 18 and member)
println(age >= 18 or member)
println(not member)
println(age >= 18 and not member)
```
**Output:**

```
false
true
true
true
```

## if

`if` chooses between blocks. A block is a set of lines indented two spaces, and the block ends when the indentation does:

```moxie
temperature = 31
if temperature > 30
  println("hot")
  println("stay inside")
println("done")
```
**Output:**

```
hot
stay inside
done
```

With `elif` and `else` you get more branches, and the first one whose condition holds runs:

```moxie
score = 75
if score >= 90
  println("A")
elif score >= 70
  println("C or better")
else
  println("keep trying")
```
**Output:**

```
C or better
```

## if gives a value

An `if` is an expression, so it can produce a value. Each branch's last line is its value, and an `else` is required so there is always one:

```moxie
score = 85
grade = if score >= 90
  "A"
elif score >= 80
  "B"
else
  "C"
println(grade)
```
**Output:**

```
B
```

When each branch is short, the whole chain goes on one line with `then`:

```moxie
score = 85
grade = if score >= 90 then "A" elif score >= 80 then "B" else "C"
println(grade)
```
**Output:**

```
B
```

A chain is all on one line or all in blocks; you can't mix the two. If the branches have different types, the compiler rejects it, because `grade` would have no single type:

```moxie
x = if true then 1 else "one"
```
**The compiler says:**

```
error: the branches of this `if` have different types: `Int` and `String`
```

Without a final `else`, the `if` can only be used as a statement, and every branch must do something rather than produce a value.

## A guard at the end of a line

An action can end with `if`, which runs it only when the condition holds. It reads well for checks:

```moxie
attempts = 5
println("retrying") if attempts > 3
println("quiet") if attempts > 9
println("done")
```
**Output:**

```
retrying
done
```

## when

`when` compares one value against several *patterns*, top to bottom, and runs the first that matches. The last arm is `else`, which matches anything:

```moxie
day = 3
name = when day
  1 -> "Monday"
  2 -> "Tuesday"
  3 -> "Wednesday"
  else "another day"
println(name)
```
**Output:**

```
Wednesday
```

An arm is a pattern, an arrow, and what to do. `when` is an expression too, so `name` got the value of the arm that matched. A pattern can be several alternatives with `|`, a range with `in`, or a comparison:

```moxie
fn describe(n Int) String
  when n
    0 -> "zero"
    1 | 2 | 3 -> "a few"
    in 4..9 -> "several"
    >= 10 -> "many"
    else "negative"
println(describe(0))
println(describe(2))
println(describe(7))
println(describe(50))
println(describe(-5))
```
**Output:**

```
zero
a few
several
many
negative
```

`when` with no value in front tests conditions in order, which is a tidy replacement for a long `elif` chain:

```moxie
n = 25
when
  n < 0 -> println("negative")
  n % 2 == 0 -> println("even")
  else println("odd and positive")
```
**Output:**

```
odd and positive
```

A number is not text and text is not a number, so a pattern of the wrong kind is an error, not a silent non-match. Patterns can do much more, taking apart tuples, lists, and enums, and the lesson on patterns covers them.

## Early exit

Inside a function, `return` leaves at once. It is the usual way to handle the unusual case first and keep the main path flat:

```moxie
fn describe(score Int) String
  if score < 0
    return "invalid"
  if score >= 90 then "A" else "B"
println(describe(-1))
println(describe(95))
println(describe(70))
```
**Output:**

```
invalid
A
B
```

The last expression of a function is its result, so the final `if` needs no `return`. A `return` on the last line is redundant, and the compiler warns about it. The lesson on functions comes soon.

---

[← Templates and locales](59-fmt-and-locales.html) · [Contents](./) · [Loops →](07-loops.html)
