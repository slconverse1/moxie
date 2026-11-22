---
layout: default
dialect: gc
learn: true
title: "Recursion and function clauses · Mixer’s Guide moxie/gc"
---
<p><small>Functions</small></p>

# 12. Recursion and function clauses

A function that calls itself is *recursive*. Recursion is the natural way to work through data that is built from smaller pieces of the same kind, and in moxie it is cheap enough to use freely.

## A recursive function

The factorial of `n` is `n` times the factorial of `n - 1`, and the factorial of 0 is 1. That definition is already a function:

```moxie
fn factorial(n Int) Int
  if n <= 1
    1
  else
    n * factorial(n - 1)
println(factorial(5))
println(factorial(10))
```
**Output:**

```
120
3628800
```

Every recursive function needs a *base case* that stops the recursion (here `n <= 1`), and every recursive call has to move toward it.

## Writing the cases separately: clauses

Moxie lets you write a function as several *clauses*, each handling one case, with a pattern in the parameter position. A literal in a parameter matches only that value:

```moxie
fn route_status(200) String = "Success"
fn route_status(404) String = "Not Found"
fn route_status(_) String = "Unknown Error"
println(route_status(200))
println(route_status(404))
println(route_status(500))
```
**Output:**

```
Success
Not Found
Unknown Error
```

The clauses are tried from the top, and the first whose patterns match is used. `_` matches anything, so it makes a good last clause. The same function written with `when` would say exactly the same thing; clauses read better when each case is one line.

A clause can use a name to bind its argument, and it can refer to the other parameters:

```moxie
fn sum_to(0, total Int) Int = total
fn sum_to(n, total Int) Int = sum_to(n - 1, total + n)
println(sum_to(4, 0))
```
**Output:**

```
10
```

In the second clause, `n` has no type written, because the first clause already said that `sum_to`'s first parameter is an `Int`.

A clause can also have a *guard*, an `if` before the body:

```moxie
fn classify(n Int) String if n < 0 = "negative"
fn classify(n) if n == 0 = "zero"
fn classify(n) = "positive"
println(classify(-5))
println(classify(0))
println(classify(8))
```
**Output:**

```
negative
zero
positive
```

## Deep recursion is fine

A recursive call that is the very last thing a function does is a *tail call*, and the language promises that a tail call reuses the function's frame instead of growing the stack. That is why `sum_to` above, which carries its running total along in `total`, can count as high as you like where a version that waits for each answer (`n + sum_to(n - 1)`) would eventually run out of stack. Writing a function with an extra "accumulator" parameter, as `sum_to` does, is the standard way to turn a recursion into a tail call:

```moxie
fn sum_to(0, total Int) Int = total
fn sum_to(n, total Int) Int = sum_to(n - 1, total + n)
println(sum_to(3000, 0))
```
**Output:**

```
4501500
```

One caution about the *reference interpreter*, as opposed to the language: it is a simple tree-walking program and does not yet implement the frame reuse, so very deep recursion (tens of thousands of calls) gets slow there. The promise is part of the design and is what a compiler would deliver; for now, keep the examples you run modest.

If you want the compiler to insist that a recursion is a tail call, mark the function `tailrec`. A recursive call that isn't in tail position, like `n * factorial(n - 1)` (the multiplication happens after the call returns), becomes a compile error:

```moxie
tailrec fn factorial(n Int) Int
  if n <= 1
    1
  else
    n * factorial(n - 1)
```
**The compiler says:**

```
error: `factorial` is marked `tailrec`, but this recursive call is not in tail position
```

The tail-recursive form passes the product along instead:

```moxie
tailrec fn factorial(0, acc Int) Int = acc
tailrec fn factorial(n, acc) = factorial(n - 1, acc * n)
println(factorial(10, 1))
```
**Output:**

```
3628800
```

A loop and a tail-recursive function are two ways to say the same thing, and the compiler treats them alike. Use whichever reads better.

## Recursion over data

Recursion shines when the data is itself recursive. A list is either empty, or a first element and the rest. A pattern takes it apart:

```moxie
fn total(xs List[Int]) Int
  when xs
    List() -> 0
    List(head, ...tail) -> head + total(tail)
println(total(List(10, 20, 30)))
println(total(List()))
```
**Output:**

```
60
0
```

`List(head, ...tail)` matches a non-empty list, binding its first element to `head` and the rest to `tail`. The lesson on patterns shows everything such a pattern can do, and a later lesson shows how this same sum is written with `reduce` when you don't need the explicit recursion.

## A function that calls itself needs a bound

Every recursive definition above stops because its argument gets smaller. If it doesn't, the program runs out of stack and the running fiber aborts with a "stack overflow" diagnostic. Tail calls avoid it; others are limited by the stack, which is large but finite.

*In the Spec: [8. Patterns and `when`](../spec.html#s8), [9. Functions](../spec.html#s9)*

---

[← Anonymous functions and closures](09-lambdas-and-closures.html) · [Contents](./) · [Generic functions →](11-generics.html)
