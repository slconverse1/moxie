---
layout: default
dialect: gc
title: "Types that compute · Learn moxie/gc"
---
<p><small>Designing with interfaces</small></p>

# 46. Types that compute

Types in moxie can be built and taken apart by small programs of their own. This is an advanced lesson. You don't need any of it to write ordinary programs, but it explains how the language's generic library is typed, and it lets you write functions whose result type depends on their arguments.

## Type lambdas

A hole fixes only the first argument of a type, so `Result[_, String]` can't say "a `Result` whose error comes first". A **type lambda** can: `[A] -> Result[String, A]` is a function from a type to a type, written with the brackets, the arrow, and the result. Hand one to a constructor parameter and it becomes the constructor it names:

```moxie
fn one[M[_] Monad]() M[Int]
  M.pure(1)
type Fail[A] = Result[A, String]
println("${one[[A] -> Result[A, String]]()} ${one[Fail]()}")
x ([A] -> Result[A, String])[Int] = Ok(3)
println(x)
```
**Output:**

```
Ok(1) Ok(1)
Ok(3)
```

A generic alias such as `Fail` is a type lambda with a name. The lambda is replaced by its body when it's used, so nothing about it exists at run time, and it never loops, because a lambda can't refer to itself.

Mistakes: giving a two-parameter lambda where `F[_]` wants one (the compiler reports the arity), and applying a lambda to the wrong number of types.

## Type functions

A type lambda only substitutes. When a type has to be *taken apart*, write a type alias whose body is a `when`, with an arm for each shape:

```moxie
type Elem[T] = when T
  List[X] -> X
  Array[X][N] -> X

type Concat[A, B] = when A
  () -> B
  (H, ...T) -> (H, ...Concat[T, B])

type Length[T] = when T
  () -> 0
  (H, ...Rest) -> 1 + Length[Rest]

fn head_of(xs Array[Int][3]) Elem[Array[Int][3]]
  xs(0)
joined Concat[(Int, String), (Bool,)] = (1, "a", true)
sized Array[Int][Length[(Int, String)]] = Array(1, 2)
println("${head_of(Array(7, 8, 9))} ${joined(1)} ${sized(1)}")
```
**Output:**

```
7 a 2
```

`Elem[Array[Int][3]]` is `Int`, because the first arm that matches wins.

- A bare name in a pattern that isn't a known type (`X`, `N`, `H`) is a variable the match binds.
- `...Rest` binds the remaining items of a tuple type, as `...rest` does in a list pattern.
- Numbers are types, so `Length` counts, and `Array[X][N - 1]` computes a size.
- An arm may have a guard, `M if M > 3 -> Array[Int][M]`, and a string in quotes is a type too, so a schema can be written `"id" -> Int`, `"name" -> String`.
- An alias may call itself, so a type function can loop over a tuple type.

Because that makes the type language a program, the checker limits it: a use that takes more than 64 reductions (`type_fuel` under `[program]` in `Moxie.toml` changes the number) or a type that grows past 4,000 parts is an error that shows the last few steps, and a function that calls itself on a type that isn't a piece of what it matched gets a warning. If no arm matches, the compiler says which type had no arm. Inside a generic function the type isn't known yet, so `Elem[T]` waits until the call. A type function exists only while the program is checked.

Mistakes: an arm that doesn't shrink (it ends only at the limit), and expecting a pattern name to mean a type you declared later in the file (a name that's already a type is a constant, not a variable).

### Field names at the type level

Tuple types keep their field names, and an arm can look a field up by name. With `type Get[R, K] = when R` and the arms `(K T, ...Rest) -> T` and `(_ _, ...Rest) -> Get[Rest, K]`, a function `fn get[R, K](row R, key K) Get[R, K]` called as `get(user, "name")` returns `String` and as `get(user, "zip")` returns `Int`, and `get(user, "nope")` is an error because no arm matches. A literal argument keeps its own type (`"name"`, `3`) when its parameter is used inside a type function; otherwise it's widened to `String` or `Int` as before.

### Asking what a type can do

An arm may use a bound as its pattern: `X Named -> String` matches any type that implements `Named` and binds it to `X`, so `type Label[T] = when T` with the arms `X Named -> String` and `else Int` gives `String` for a type with an `impl Named` and `Int` for the rest. This is the type-level form of `[T Named]`, and it reuses the `impl` and `deriving` you already wrote.

### Intersections

`any Named + Aged` is a value that implements both interfaces, written with the `+` that joins bounds (`[T Equatable + Show]`). `describe(Dog(...))` is a compile error when `Dog` has no `impl Aged`, and a type-function arm can ask the same, `X Named + Aged -> String`.

## Compile-time evaluation

A pure function that you declare is also run by the compiler when its arguments are constants and a constant is needed. `N = fib(6)` makes `N` usable as a size, and a wrong size is caught before the program runs:

```moxie
pure fn fib(n Int) Int
  when n
    0 -> 0
    1 -> 1
    else fib(n - 1) + fib(n - 2)

a Array[Int][fib(5)] = Array(1, 2, 3)
println(a)
```
**The compiler says:**

```
error: mismatched types: expected `Array[Int][5]`, found `Array[Int][3]`
```

And with the right size:

```moxie
pure fn fib(n Int) Int
  when n
    0 -> 0
    1 -> 1
    else fib(n - 1) + fib(n - 2)

N = fib(6)
a Array[Int][N] = Array(1, 1, 2, 3, 5, 8, 13, 21)
println(len(a))
```
**Output:**

```
8
```

Nothing special is written: there's no keyword, and a function with a print or other effect is simply left until run time. A call that never finishes is stopped (`eval_fuel` in `[program]` sets the step limit).

## What to remember

- A type lambda `[A] -> Result[String, A]` is a function from a type to a type; a generic alias is one with a name.
- A type function is an alias whose body is a `when` over types; it can count, look up fields by name, and loop.
- The checker limits type-level work (`type_fuel`), and all of it vanishes at run time.
- A pure function whose arguments are constants is run by the compiler when a constant is needed, such as an array size.

---

[← Typeclasses](46-typeclasses.html) · [Contents](./) · [Properties, field delegates, and proxies →](48-properties-delegates-proxies.html)
