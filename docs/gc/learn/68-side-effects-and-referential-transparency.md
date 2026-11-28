---
layout: default
dialect: gc
learn: true
title: "Side effects and referential transparency · Moxie/gc Mixer’s Guide"
---
# 67. Side effects and referential transparency

A pure function's call can stand for its result. Anywhere `square(4)` appears, `16` would do the same job, and the reader never needs to run the program to know what it means. That property is called *referential transparency*, and the reasoning in the earlier lessons depends on it. A function that prints, reads a file, or changes something outside itself has a *side effect*, and then a call can't be swapped for a value, because running it again may do something different.

## Swapping a call for its value

```moxie
fn square(x Int) Int
  x * x

println(square(4) + square(4))
println(16 + 16)
```
**Output:**

```
32
32
```

Both lines print the same thing. Because `square` is pure, the two programs are interchangeable.

## Effects make a call more than a value

A function declared `impure` may print, read or write, and each call runs its effects again.

```moxie
impure fn greet(name String) String
  println("hello, $name")
  name

a = greet("ann")
b = greet("ann")
println(a + b)
```
**Output:**

```
hello, ann
hello, ann
annann
```

Each call printed a line, so the two calls are not the same thing as one call with its result copied. The compiler knows which functions are impure, and it marks the call sites that need the effects.

## The compiler keeps the two apart

Some places need a pure function. A lambda written without `fn` must be pure, so it can't call an impure function:

```moxie
impure fn greet(name String) String
  println("hello, $name")
  name

xs = List("ann", "bob") |> map()(n) -> greet(n) |> collect()
println(xs)
```
**The compiler says:**

```
a lambda must be pure
```

When a function may have effects, write it as an anonymous `fn`, with its body indented below, or declare it with `fn` and `impure`. That tells the reader what to expect at the call.

## What referential transparency buys

Because a pure call can be replaced, the compiler and the reader can both reason about it:

- **Reuse without a surprise.** A pure value can be computed once and shared. The program means the same thing either way.
- **Caching is safe.** A table of answers to a pure function can be filled in once and read later. Caching an impure call would skip its effects, so moxie doesn't cache for you.
- **Constants are evaluated early.** Moxie runs pure functions at compile time when their results are needed as constants, and it refuses an impure one there.

## What to remember

- A pure call equals its result, so you can replace it with that result.
- An `impure` function does its effects on every call, and nothing else can replace it.
- A lambda written without `fn` must be pure. Use an anonymous `fn` for a function that prints or touches the world.
- Keep the pure parts of a program big, and the effects at the edges.

---

[← …moxie: the rest of the moxie toolbox](66-the-rest-of-moxie.html) · [Contents](./) · [Eager and lazy evaluation →](69-eager-and-lazy-evaluation.html)
