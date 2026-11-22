---
layout: default
title: "Generic functions · Learning Guide moxie"
---
<p><small>Functions</small></p>

# 13. Generic functions

A function that works the same way whatever the type of its argument can be written once. Such a function is *generic*, and it lists *type parameters* in square brackets after its name.

## A type parameter

This function swaps the two halves of a pair, whatever types they have:

```moxie
fn swap_pair[A, B](p (A, B)) (B, A)
  (p(1), p(0))
s = swap_pair((1, "one"))
println("${s(0)} ${s(1)}")
```
**Output:**

```
one 1
```

The compiler checks a generic function once, as written, for *every* possible `A` and `B`. A body that returned `p` unchanged would be rejected, because `(A, B)` is not the declared `(B, A)`:

```moxie
fn swap_pair[A, B](p (A, B)) (B, A)
  p
```
**The compiler says:**

```
error: mismatched types: expected `(B, A)`, found `(A, B)`
```

Calling it looks like any other call. The compiler fills `A` and `B` in from the arguments, and builds one specialized copy of the function for each use, so a generic function costs nothing extra at run time.

## Inference goes left to right

The compiler works out the type parameters from the arguments in order. A literal takes its type from what is already known:

```moxie
fn apply_twice[T](x T, f (T) -> T) T
  f(f(x))
println(apply_twice(3, (n) -> n * 2))
println(apply_twice("ab", (s) -> s + "!"))
```
**Output:**

```
12
ab!!
```

Here `3` fixes `T` as `Int`, so the lambda's `n` is an `Int` without being annotated.

When nothing in the arguments fixes a type parameter, write it out in brackets at the call:

```moxie
x = cast[Int8](100)
println(x)
```
**Output:**

```
100
```

## Bounds: what a type has to be able to do

A generic function can't use `<` on a `T`, because not every type has an order. A *bound* says what the type must support, and the body may then use it:

```moxie
fn bigger[T Ordered](a T, b T) T
  if a < b then b else a
println(bigger(3, 9))
println(bigger("pear", "apple"))
println(bigger(2.5, 1.5))
```
**Output:**

```
9
pear
2.5
```

`Ordered` means "supports `<`, `>`, `<=`, `>=`." Without the bound, the compiler refuses:

```moxie
fn bigger[T](a T, b T) T
  if a < b then b else a
```
**The compiler says:**

```
needs an `Ordered` bound
```

A parameter can have several bounds, joined with `+`:

```moxie
fn show_max[T Ordered + Equatable](a T, b T) String
  if a == b then "same" else "max is ${if a < b then b else a}"
println(show_max(3, 9))
println(show_max(4, 4))
```
**Output:**

```
max is 9
same
```

The prelude bounds are `Equatable` (`==`), `Ordered` (order), `Hashable` (usable as a Dict key or in a Set), `Show` (can be printed), `Read` (can be parsed from text), `Addable` (`+`), and `Numeric` (arithmetic). You can define your own bounds with interfaces, which have their own lesson.

## Generic functions are everywhere

Most of the built-in functions you have used are generic: `println` takes any `T` that can be shown, `max` any ordered type, and `map` works for any element type. Writing your own follows the same pattern, and a generic function can be used as a value when its type is fixed, either by writing the parameters (`f = swap_pair[Int, String]`) or by an expected type.

## Sizes as parameters

A type parameter can also be a *size*, a number that sizes a fixed-size collection. The lesson on arrays shows that; the point to remember here is that a size in brackets is read as an `Int` inside the function, and a `where` clause can limit it (`N where N > 0`).

---

[← Recursion and function clauses](10-recursion-and-clauses.html) · [Contents](./) · [Tuples →](12-tuples.html)
