---
layout: default
dialect: gc
title: "Anonymous functions and closures · Learning Guide moxie/gc"
---
<p><small>Functions</small></p>

# 11. Anonymous functions and closures

A function doesn't need a name. An *anonymous function*, which many languages call a lambda, is written `(parameters) -> body`. In these lessons the two words mean the same thing. What makes it anonymous is the missing name, not its size.

## Writing one

```moxie
double = (n Int) -> n * 2
println(double(21))
```
**Output:**

```
42
```

`double` is now bound to a function value, and it is called like any function. A function is a value like any other: it can be bound to a name, passed to another function, returned from one, and kept in a collection.

When the compiler can tell the parameter types from the context, you can leave them out. That is the usual situation when a lambda is passed to a function like `map`:

```moxie
numbers = List(1, 2, 3, 4)
squares = numbers.map((n) -> n * n).collect()
println(squares)
```
**Output:**

```
List(1, 4, 9, 16)
```

A lambda body can also be a block of several lines. Indent it under the arrow, and its last expression is the result:

```moxie
describe = (n Int) ->
  parity = if n % 2 == 0 then "even" else "odd"
  "$n is $parity"
println(describe(7))
println(describe(10))
```
**Output:**

```
7 is odd
10 is even
```

## Function types

A function's type is written like its parameters, an arrow, and its result. `(Int) -> Int` takes an `Int` and gives an `Int`, and `(Int, Int) -> Bool` takes two. You write them when you declare a function that takes or returns a function:

```moxie
fn apply_twice(f (Int) -> Int, x Int) Int
  f(f(x))
println(apply_twice((n) -> n + 10, 1))
println(apply_twice((n) -> n * 3, 2))
```
**Output:**

```
21
18
```

## Shorter forms

When a lambda is as simple as "do this to the argument", a placeholder `_` stands for the argument and you needn't name it:

```moxie
println(List(1, 2, 3).map(_ * 2).collect())
```
**Output:**

```
List(2, 4, 6)
```

`_1` and `_2` are the first and second arguments of a two-argument lambda, so `_1 + _2` adds two numbers:

```moxie
println(List(1, 2, 3, 4).reduce(0, _1 + _2))
```
**Output:**

```
10
```

An operator with one side missing is also a function of the other side: `(+ 1)` adds one, `(* 2)` doubles, `(> 2)` asks "is it above two":

```moxie
println(List(1, 2, 3).map((+ 1)).collect())
println(List(1, 2, 3).map((10 -)).collect())
println(List(1, 5, 9).filter((> 4)).collect())
```
**Output:**

```
List(2, 3, 4)
List(9, 8, 7)
List(5, 9)
```

`(- 1)` with a space subtracts one from its argument. `(-1)` without one is just the number negative one.

A lambda can also be written *after* a call, with its own parameter list, when that reads better than putting it inside the parentheses. That form, and the pipe `|>` that makes it natural, are in the lesson on pipelines.

## Closures

A lambda can use the names around it. When it does, the function carries those values along with it, and such a function is called a *closure*:

```moxie
factor = 5
scale = (n Int) -> n * factor
println(scale(6))
```
**Output:**

```
30
```

The closure copies the value of `factor` at the moment it's made, so changing `factor` afterward doesn't affect it. That is another consequence of values never changing: there is nothing shared to go out of step.

A function can build and return a closure, which is how you make a customized function:

```moxie
fn make_adder(k Int) (Int) -> Int
  (n) -> n + k
add10 = make_adder(10)
add100 = make_adder(100)
println(add10(5))
println(add100(5))
```
**Output:**

```
15
105
```

`make_adder(10)` returned a function that remembers `k = 10`. Calling `add10(5)` gives 15.

Only plain data can be captured: numbers, text, tuples, lists, and similar. Something that owns a resource, such as an open file, can't be captured silently. The lessons on resources and concurrency cover how those are handled.

## Pure lambdas and effects

A lambda written without `fn` is *pure*: it computes a result from its arguments and what it captured, and it can't print, read files, or use the network. That keeps it safe to pass around. To write an anonymous function that does have effects, put `fn` in front and indent the body:

```moxie
shout = fn (line String) Unit
  println(upper(line) + "!")
shout("hello")
```
**Output:**

```
HELLO!
```

An anonymous `fn` has no `->`; it is declared like a named function with the name left out.

## Currying and partial calls

A function that takes two arguments can be turned into a chain of one-argument functions with `curry`. And a call with `_` where an argument goes is a *partial call*: it makes a function waiting for the missing argument:

```moxie
fn add(x Int, y Int) Int = x + y
fn log(level String, message String) Unit
  println("[$level] $message")
add5 = curry(add)(5)
println(add5(10))
log_error = log("ERROR", _)
log_error("disk full")
```
**Output:**

```
15
[ERROR] disk full
```

## Composing functions

`~>` joins two functions left to right, and `<~` right to left:

```moxie
fn inc(x Int) Int = x + 1
fn twice(x Int) Int = x * 2
println((inc ~> twice)(5))
println((twice ~> inc)(5))
println((twice <~ inc)(5))
```
**Output:**

```
12
11
12
```

`(inc ~> twice)(5)` does `inc` first, then `twice`: (5 + 1) * 2 is 12. `(twice ~> inc)(5)` is 5 * 2 + 1.

## Functions in data

Because a function is a value, a tuple can hold one in a field, and you call it like a method:

```moxie
tuple Op
  apply (Int) -> Int
op = Op(apply: (n) -> n * 2)
println(op.apply(21))
```
**Output:**

```
42
```

A `Dict` of functions makes a dispatch table. Dictionaries have a lesson of their own, and the lesson on interfaces shows the more structured way to attach behavior to a type.

---

[← Functions](08-functions.html) · [Contents](./) · [Recursion and function clauses →](10-recursion-and-clauses.html)
