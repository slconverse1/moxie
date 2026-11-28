---
layout: default
dialect: gc
learn: true
title: "Unifying tuples and parameter lists · Moxie/gc Mixer’s Guide"
---
# 74. Unifying tuples and parameter lists

A function's parameters and a tuple are the same kind of thing in moxie. A parameter list is a sequence of typed slots, and so is a tuple. Because of that, a tuple can fill a parameter list, a function's result can feed the next function's parameters, and a list of values can be spread into a call. The rule is simple, and it has one limit that you should know.

## A tuple fills a parameter list

When a function takes two `Int`s, a single `(Int, Int)` tuple can be passed to it, and the tuple unpacks into the parameters in order:

```moxie
fn add(x Int, y Int) Int
  x + y

pair = (3, 5)
println(add(pair))
```
**Output:**

```
8
```

The spread form, `add(...pair)`, says the same thing with the dots written out, and it works on a tuple in the same way.

## A result feeds the next call

A function that returns a tuple gives you values that slide straight into a following function's parameters when the next stage is in a pipeline:

```moxie
fn add(x Int, y Int) Int
  x + y

fn split(n Int) (Int, Int)
  (n / 2, n - n / 2)

println(split(9) |> add())
```
**Output:**

```
9
```

`split` returns two numbers as one tuple, and `add` takes two numbers. The tuple unpacks into `add`'s parameters, so the pipeline needs no glue between the stages.

## A tuple can be one parameter

The other side of the same rule is that a parameter can itself be a tuple type. Then the tuple is passed as one value, and its fields are read in the body:

```moxie
fn take_pair(p (Int, Int)) Int
  p(0) * p(1)

println(take_pair((2, 6)))
```
**Output:**

```
12
```

The choice between `add(x Int, y Int)` and `take_pair(p (Int, Int))` is the choice between two parameters and one tuple parameter. Both are written with the same types, so reading the signature tells you which you have.

## Named fields follow the same rule

A tuple with named fields matches a function whose parameters have the same names and types in the same order. Here the fields of a `Point` are passed on as two arguments:

```moxie
tuple Point
  x Int,
  y Int

fn norm1(x Int, y Int) Int
  abs(x) + abs(y)

p = Point(x: -3, y: 4)
println(norm1(p.x, p.y))
```
**Output:**

```
7
```

## The limit: modifiers stop the unification

Parameter modifiers have no tuple counterpart. A parameter marked `ref`, `lazy`, or `using` is not a plain slot, so a tuple won't unpack into a list that contains one. The call below fails, because the tuple is taken as a single value for the first parameter, and nothing is left for the second:

```moxie
fn add(lazy x Int, y Int) Int
  x + y

pair = (3, 5)
println(add(pair))
```
**The compiler says:**

```
missing argument 'y'
```

Spell out the arguments when a modifier is involved: `add(pair(0), pair(1))`. The unification covers the plain parameters, and the modifiers are written out.

## What to remember

- A tuple of values matches a parameter list of the same types, in order.
- A function's result can feed the next stage of a pipeline, when its shape matches the parameters.
- A parameter may be a tuple type, and then the tuple is one value.
- Parameters marked `ref`, `lazy`, or `using` don't unify with a tuple, so write their arguments out.

---

[← Modularity and encapsulation without classes](74-modularity-and-encapsulation.html) · [Contents](./) · [Machine learning, lite →](76-machine-learning-lite.html)
