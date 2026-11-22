---
layout: default
dialect: gc
learn: true
title: "Functions · Mixer’s Guide moxie/gc"
---
# 10. Functions

<div class='specref' markdown='1'>In the Spec: [9. Functions](../spec.html#s9)</div>

A *function* is a named piece of code that takes values in and gives a value back. You have used built-in functions such as `println` and `max`. This lesson is about writing your own.

## Declaring a function

A function is declared with `fn`, a name, parameters in parentheses, and a *return type*. The body is indented under it, and the last expression in the body is the function's result:

```moxie
fn add(x Int, y Int) Int
  x + y
println(add(2, 3))
```
**Output:**

```
5
```

Each parameter is a name followed by its type, with no colon. The return type comes after the parentheses. In moxie every function states its parameter types and its return type; the compiler infers a great deal inside the body, but the *interface* of a function is always written down, so a reader never has to guess.

When the body is a single expression, it can follow an `=` on the same line:

```moxie
fn double(x Int) Int = x * 2
fn square(x Int) Int = x * x
println(double(21))
println(square(9))
```
**Output:**

```
42
81
```

Declarations are *colonless*: you never write `x: Int`. The one place a colon appears is a call that names an argument, shown next.

## Named arguments and defaults

A call can name its arguments, which makes the call self-explanatory and lets you give them in any order. A parameter can have a default value, so the caller may leave it out:

```moxie
fn greet(name String, greeting String = "Hello") String = "$greeting, $name!"
println(greet("Ada"))
println(greet("Bo", "Hi"))
println(greet("Bo", greeting: "Hi"))
println(greet(greeting: "Yo", name: "Cy"))
```
**Output:**

```
Hello, Ada!
Hi, Bo!
Hi, Bo!
Yo, Cy!
```

Positional arguments come first, then named ones. Each parameter can be given only once, and parameters with defaults must come last. The colon here marks a *value* in a call; a declaration never has one.

A bare name after a named argument stands for itself: `greet(name: "Ada", greeting)` means `greeting: greeting`.

## Functions with no result

A function that does something, like printing, rather than computing a value, returns `Unit`. `Unit` is the type with exactly one value, written `()`:

```moxie
fn announce(msg String) Unit
  println("** $msg")
announce("starting")
result = announce("again")
println(result)
```
**Output:**

```
** starting
** again
()
```

If a `Unit` function ends with an expression that isn't `Unit`, the compiler complains, because a value would be silently thrown away:

```moxie
fn f(x Int) Unit
  x + 1
```
**The compiler says:**

```
error: mismatched types: expected `Unit`, found `Int`
```

## Returning several values

A function returns one value, and that value can be a *tuple* holding several. The caller takes the pieces apart with a tuple binding:

```moxie
fn divmod(a Int, b Int) (Int, Int) = (a / b, a % b)
quotient, remainder = divmod(17, 5)
println("$quotient r $remainder")
println(divmod(17, 5))
```
**Output:**

```
3 r 2
(3, 2)
```

A tuple field is read by position: `divmod(17, 5)(0)` is the first. The lesson on tuples shows named fields, which are clearer than positions.

## Any number of arguments

A final parameter written with `...` takes any number of arguments, which the function sees as an array:

```moxie
fn total(base Int, numbers ...Int) Int
  numbers |> reduce(base, _1 + _2)
println(total(100, 1, 2, 3))
println(total(100))
```
**Output:**

```
106
100
```

`reduce` combines a sequence into one value, and `_1 + _2` is a short form of a two-argument function. Both get lessons of their own.

## Changing a caller's variable: ref

A parameter normally receives a copy of the value, so a function can't change the caller's variable. A `ref` parameter is the exception, and the call has to say so too, which keeps the effect visible at the call site:

```moxie
fn bump(ref counter Int) Unit
  counter += 1
n = 1
bump(ref n)
bump(ref n)
println(n)
```
**Output:**

```
3
```

Forgetting `ref` at the call is an error:

```moxie
fn bump(ref counter Int) Unit
  counter += 1
n = 1
bump(n)
```
**The compiler says:**

```
error: parameter `counter` is `ref`; write `ref n`
```

## A function sees only what is above it

A function can use only names bound *above* it in the file, plus its own parameters. It can't reach a name bound further down or in another function. So a function's behavior depends on its arguments and on definitions it can see, which is what makes functions easy to reason about:

```moxie
rate = 5
fn with_rate(x Int) Int = x * rate
println(with_rate(10))
```
**Output:**

```
50
```

A top-level name that a function has read can't be rebound afterward, because that would quietly change what the function means:

```moxie
rate = 5
fn with_rate(x Int) Int = x * rate
rate = 6
println(with_rate(10))
```
**The compiler says:**

```
error: `rate` is read by function `with_rate` (line 2), so this later binding would not be the one it sees: give it a new name
```

## Order of definitions

A function has to be declared before it is used, the same rule as for a name:

```moxie
fn a(n Int) Int
  b(n)
fn b(n Int) Int
  n
println(a(1))
```
**The compiler says:**

```
error: `b` is used before its declaration (line 3): move it up, or write `forward fn b(...)` first
```

Moving `b` above `a` fixes it. When two functions call each other, neither can go first, so one is announced ahead of time with `forward fn`, which is just its signature:

```moxie
forward fn is_odd(n Int) Bool
fn is_even(n Int) Bool
  if n == 0 then true else is_odd(n - 1)
fn is_odd(n Int) Bool
  if n == 0 then false else is_even(n - 1)
println(is_even(10))
println(is_odd(10))
```
**Output:**

```
true
false
```

A function that calls itself is *recursive*, and the lesson on recursion shows how moxie keeps even very deep recursion cheap.

## Pure and impure

A function that only computes from its arguments is *pure*: given the same arguments it gives the same result, and it affects nothing else. A function that prints, reads a file, or talks to a network has effects. Moxie keeps the two apart at the type level: the compiler works out what a function does, and refuses to use an effectful function where a pure one is required, such as in a lambda written without `fn`, or in a constant evaluated at compile time. You will see that rule in the next lesson.

---

[← Loops](07-loops.html) · [Contents](./) · [Anonymous functions and closures →](09-lambdas-and-closures.html)
