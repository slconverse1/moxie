---
layout: default
learn: true
title: "Loops · Learning Guide moxie"
---
<p><small>Getting started</small></p>

# 9. Loops

To do something many times, use a loop. Moxie has one loop keyword, `for`. It walks over a collection or a range, and it repeats until a condition fails. A loop is an expression, so a loop can produce a value, which this lesson gets to after the basics.

## for

`for x in something` runs its block once for each element:

```moxie
for fruit in List("apple", "pear", "plum")
  println("I like $fruit")
```
**Output:**

```
I like apple
I like pear
I like plum
```

`List(...)` builds a list, which has its own lesson. A *range* walks a run of integers: `1..5` includes the end, and `1..<5` stops before it:

```moxie
for i in 1..3
  println("up $i")
for i in 0..<3
  println("index $i")
```
**Output:**

```
up 1
up 2
up 3
index 0
index 1
index 2
```

A step is written after the range. A negative step counts down:

```moxie
for i in 10..<1 step -4
  println(i)
for i in 0..10 step 5
  println(i)
```
**Output:**

```
10
6
2
0
5
10
```

A range of characters walks too:

```moxie
for c in 'a'..'e'
  print(c)
println()
```
**Output:**

```
abcde
```

To get the position along with the element, `enumerate()` gives `(index, value)` pairs, and a binding with two names takes each pair apart:

```moxie
for i, name in List("Ann", "Bo").enumerate()
  println("$i: $name")
```
**Output:**

```
0: Ann
1: Bo
```

## for on a condition

`for condition` (a header with no `in`) repeats its block as long as the condition is true:

```moxie
n = 1
for n < 100
  println(n)
  n = n * 3
```
**Output:**

```
1
3
9
27
81
```

Look at what happened to `n`. Inside the loop, `n = n * 3` is a new binding of `n` for the next pass, and the loop carries it forward the way a function call carries its arguments. So a loop on a condition counts as you'd hope. What it doesn't do is change the `n` that exists *after* the loop: that one is still `1`, and the compiler tells you so if you read it there. The loop's value (below) and `name@1` (also below) are the two ways to get a result out. To loop until something breaks out of it, write `for true`. There is no `while`: writing it is an error that says to write `for`.

A condition that is a test on a pattern ends a loop at the end of a stream of input. `read_line()` gives `Err` at end of file, so this reads every line:

```moxie
for read_line() is Ok(line)
  println("got ${line}")
```

A header with an `in` at its top level is the iteration form, `for x in xs`. So a condition that is itself a membership test is written in brackets:

```moxie
allowed = Set(1, 2)
n = 1
for (n in allowed)
  println(n)
  n = n + 1
```
**Output:**

```
1
2
```

If you write `for n in allowed` while an `n` already exists, you get a note: that form binds a new `n` for each element, and it does not test the old one.

## break and continue

`break` leaves the loop, and `continue` skips to the next pass:

```moxie
for n in 1..10
  if n % 2 == 1
    continue
  if n > 6
    break
  println("even $n")
```
**Output:**

```
even 2
even 4
even 6
```

## A loop produces a value

A loop is an expression, and `break(value)` is how it gives one. The loop's `else` is what you get when it ran to the end without breaking. Here the loop searches for the first number over ten:

```moxie
xs = List(4, 8, 15, 16)
found = for x in xs
  if x > 10
    break(x)
else
  -1
println(found)
```
**Output:**

```
15
```

Look at where the `else` sits. It is lined up with `for`, so it belongs to the loop. An `else` lined up with the `if` would be a different one. With no number over ten, the loop falls through to its `else`:

```moxie
xs = List(4, 8, 9)
found = for x in xs
  if x > 10
    break(x)
else
  -1
println(found)
```
**Output:**

```
-1
```

A loop on a condition works the same way, and a loop used only for its effects can have an `else` too. It runs when the loop finishes without a `break`:

```moxie
for x in List(1, 2, 3)
  println(x)
else
  println("ran out")
for x in List(1, 2, 3)
  if x == 2
    break
else
  println("not printed")
println("end")
```
**Output:**

```
1
2
3
ran out
end
```

## Updating a name from inside a loop

Because a name bound inside a block is a new, local name, a loop body can't update a name from outside by plain assignment. Say what you mean with `name@1`, which reaches the binding one block out:

```moxie
total = 0
count = 0
for score in List(70, 85, 90)
  total@1 += score
  count@1 += 1
println("$total $count")
```
**Output:**

```
245 3
```

That is direct but a little mechanical. When the loop computes *one* value, it is usually better to let the value carry the state, with `reduce`, which a later lesson on streams covers:

```moxie
total = List(70, 85, 90) |> reduce(0, (acc, s) -> acc + s)
println(total)
```
**Output:**

```
245
```

## Nested loops and labels

A `break` leaves the innermost loop. To leave an outer one, give it a label, written `#name` before the loop, and use `break #name`. `continue #name` works the same way:

```moxie
rows = List(List(1, 2), List(3, -1), List(5, 6))
#outer for row in rows
  for cell in row
    if cell < 0
      break #outer
    println(cell)
```
**Output:**

```
1
2
3
```

```moxie
rows = List(List(1, -2), List(3, -1), List(4))
#outer for row in rows
  for cell in row
    if cell < 0
      continue #outer
    println(cell)
```
**Output:**

```
1
3
4
```

## When the loop is the whole point of the function

A function that loops and returns the result is just a loop whose value is the function's value. The loop's `else` runs when the condition turns false, and it can see the carried `n`:

```moxie
fn first_square_over(limit Int) Int
  n = 1
  for n * n <= limit
    n = n + 1
  else
    n * n
println(first_square_over(50))
```
**Output:**

```
64
```

Reading `n` after the loop, instead of in the `else`, is the mistake the compiler catches:

```moxie
fn first_square_over(limit Int) Int
  n = 1
  for n * n <= limit
    n = n + 1
  n * n
println(first_square_over(50))
```
**The compiler says:**

```
error: `n` is changed inside the loop (line 4) only for the loop's own condition, so here it still has its old value: write `n@1` in the loop to change this one, or give it back with `else n`
```

Moxie has no `forEach`, `map` loop statement, or `do ... while`. A `for` with `continue` covers the first, streams cover the second, and a `for true` with a `break` covers the third. Streams and their pipelines get a lesson of their own.

*In the Spec: [18. Fibers, loops, streams](../spec.html#s18), [18a. Labels and exits](../spec.html#s18a)*

---

[← Truth and choices](06-truth-and-choices.html) · [Contents](./) · [Functions →](08-functions.html)
