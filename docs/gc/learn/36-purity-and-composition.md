---
layout: default
dialect: gc
learn: true
title: "Values, purity, and composing functions · Moxie/gc Mixer’s Guide"
---
# 45. Values, purity, and composing functions

In the Spec: [14. Caching, memoization, and effects](../spec.html#s14), [23. Functional programming support](../spec.html#s23)
{: .specref}

Moxie's functional features are ordinary code on top of a few language features: immutable values, higher-order functions, pipelines, and interfaces over type constructors. This lesson covers the first and the oldest ideas: values that never change, functions that say what they do, and functions built out of functions.

## Values never change

Every update gives a *new* value, and a name is rebound, never mutated. The old value stays valid:

```moxie
old = List(1, 2, 3)
new = old + 4
println("${len(old)} ${len(new)}")
println(old)
println(new)
```
**Output:**

```
3 4
List(1, 2, 3)
List(1, 2, 3, 4)
```

When the old value is dead afterwards, the compiler updates in place, so immutability costs no copying in the common case. `moxie build --report` lists the exceptions.

## Pure functions, and what a function does

The compiler works out for itself which functions can park, print, or use a resource. You are never required to write that, and you never pass it up the call chain: a caller of a function that prints is inferred to print, and you change nothing in the callers when you add a `println` while debugging.

When you want the compiler to hold you to a statement, declare it before `fn`: `pure`, `prints`, `parks` (both can be given, as in `prints parks fn`), or `impure` for "has some effect". A violation is a compile error that names the call:

```moxie
pure fn area(w Int, h Int) Int
  w * h

pure fn noisy(w Int) Int
  println("w is ${w}")
  w

println(area(3, 4))
```
**The compiler says:**

```
error: pure fn 'noisy' prints (calls 'println')
```

A declaration is an agreement checked *both ways*. The compiler rejects a body that does an effect you didn't declare, and it also rejects a declaration the body no longer earns, so a stale `prints` can't linger after the print is removed:

```moxie
prints fn quiet(x Int) Int
  x + 1

println(quiet(1))
```
**The compiler says:**

```
error: fn 'quiet' is declared prints but never does
```

Using a resource counts as an effect: creating, closing, or changing a channel, timer, future, or atom (and reading an atom with `@`) is not allowed in a `pure fn`, because shared state isn't pure. `dbg` and `trace` are exempt: `trace("got here")` writes to the error stream, doesn't count as an effect, and is removed in release builds, while `println` is real output and does count.

An interface member can be declared the same way (`prints fn log(self, s String) Unit`). It then becomes an upper bound: an implementation may do less, but doing more is a compile error, and code that calls through the interface is checked against the declaration.

## Functions as values

A function is a value, so it can be passed, returned, and put in a collection. `~>` *composes* two functions, left to right:

```moxie
fn inc(x Int) Int = x + 1
fn twice(x Int) Int = x * 2
fn square(x Int) Int = x * x

pipeline = inc ~> twice ~> square
out List[Int][3] = List(1, 2, 3) |> map(pipeline) |> collect()
println("${pipeline(2)} ${out(0)} ${out(1)} ${out(2)}")
```
**Output:**

```
36 16 36 64
```

`pipeline(2)` is `square(twice(inc(2)))`, which is 6 squared. A list of plain functions can also be folded over a value:

```moxie
fn inc(x Int) Int = x + 1
fn twice(x Int) Int = x * 2
fn square(x Int) Int = x * x

steps Array[(Int) -> Int] = (inc, twice, square)
result = steps |> reduce(0)(acc, f) -> f(acc)
println(result)
```
**Output:**

```
4
```

(0 becomes 1, then 2, then 4.)

## Currying

`curry` turns a function of several arguments into one that takes them one at a time, so supplying only some of them gives a new function. Closures carry data with them:

```moxie
fn add(a Int, b Int) Int = a + b

add5 = curry(add)(5)
make_adder = (k Int) -> (n Int) -> n + k
println("${add5(1)} ${make_adder(10)(1)}")
```
**Output:**

```
6 11
```

A closure that captures data can be passed and returned, but not stored in a data structure (lesson 11).

### `uncurry[n]`

`uncurry` is the inverse: it turns a function that takes its arguments one at a time back into one that takes them all at once, so it can go where an ordinary multi-argument function is expected.

You write the number of arguments in brackets, because from a type like `A -> B -> C` the compiler can't tell whether `B -> C` is the rest of a chain or a function that a one-parameter function returns:

```moxie
fn add(a Int, b Int) Int = a + b
fn add4(a Int, b Int, c Int, d Int) Int = a + b + c + d

add_c = curry(add)
println(zip_with(uncurry[2](add_c), List(1, 2, 3), List(10, 20, 30)) |> collect())
println(uncurry[4](curry(add4))(1, 2, 3, 4))
```
**Output:**

```
List(11, 22, 33)
10
```

`n` is a constant of 2 or more, and calling the result with a different number of arguments is an error. You won't need `uncurry` often, because an argument list and a tuple of the same shape are already the same thing: a two-parameter function is called as `f(a, b)` or `f(pair)`, and `f(...pair)` always unpacks.

## What to remember

- Updates make new values; old ones stay valid.
- `pure`, `prints`, `parks`, `impure` before `fn` are promises the compiler checks both ways.
- `f ~> g ~> h` composes left to right.
- `curry(f)(a)` fixes the first argument; `uncurry[n]` goes the other way.
- Capturing closures can be passed around, but not stored in data structures.

---

[← Databases with SQL](35-sql.html) · [Contents](./) · [Mapping, sequencing, and combining: functors, applicatives, and monads →](37-functors-and-monads.html)
