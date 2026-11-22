---
layout: default
dialect: gc
title: "GADTs and typestate · Learning Guide moxie/gc"
---
<p><small>Functional programming</small></p>

# 52. GADTs and typestate

Lesson 49 got a typed evaluator by making the interpreters types, and lesson 50 got one by making the nodes generic. A third way keeps one ordinary `enum` and lets each case state its own *result type* after its parameters. That is a GADT, a generalized algebraic data type.

## A typed evaluator

```moxie
enum Value[T]
  Num(n Int) Value[Int]
  Flag(b Bool) Value[Bool]
  Add(a Value[Int], b Value[Int]) Value[Int]
  Eq(a Value[Int], b Value[Int]) Value[Bool]
  If(c Value[Bool], t Value[T], e Value[T])

fn eval[T](v Value[T]) T = when v
  Num(n) -> n
  Flag(b) -> b
  Add(a, b) -> eval(a) + eval(b)
  Eq(a, b) -> eval(a) == eval(b)
  If(c, t, e) -> if eval(c) then eval(t) else eval(e)

println(eval(Add(Num(1), Num(2))))
println(eval(If(Eq(Num(1), Num(1)), Num(5), Num(6))))
```
**Output:**

```
3
5
```

A case with no result type (`If`) means `Value[T]`. Three things follow.

- **A constructor call has the type its case states.** `Num(1)` is a `Value[Int]` and `Flag(true)` is a `Value[Bool]`. So `Add(Num(1), Flag(true))` is a compile error (*expected `Value[Int]`, found `Value[Bool]`*), where a plain enum would accept it and fail when run.
- **A `when` arm learns something about `T`.** In the `Num` arm `T` is `Int`, so the arm may return `n`, and in the `Flag` arm it is `Bool`. An arm that returns the wrong type (`Num(n) -> true`) is an error. The fact holds only inside that arm.
- **Impossible cases drop out.** For a `Value[Int]`, `Flag` and `Eq` can never occur, so a `when` needs only `Num`, `Add`, and `If`, and an arm for `Flag` is an error (*can never match*). For a `Value[T]` with `T` unknown, every case is needed.

Nothing changes at run time: types are erased, so a `Value` is the same enum value it would be without the result types.

Here is the first of those errors:

```moxie
enum Value[T]
  Num(n Int) Value[Int]
  Flag(b Bool) Value[Bool]
  Add(a Value[Int], b Value[Int]) Value[Int]

x = Add(Num(1), Flag(true))
println("built")
```
**The compiler says:**

```
error: mismatched types: expected `Value[Int]`, found `Value[Bool]`
```

## Case variables and existentials

A case may use type variables of its own, written as one-letter names that the enum doesn't declare. Two shapes are useful:

```moxie
enum Value[T]
  Num(n Int) Value[Int]
  Flag(b Bool) Value[Bool]
  Pair(a Value[A], b Value[B]) Value[(A, B)]
  Packed(v Value[A], f (A) -> String) Value[String]

fn eval[T](v Value[T]) T = when v
  Num(n) -> n
  Flag(b) -> b
  Pair(a, b) -> (eval(a), eval(b))
  Packed(v, f) -> f(eval(v))

println(eval(Pair(Num(1), Flag(true))))
println(eval(Packed(Num(41), (n) -> "n=${n + 1}")))
```
**Output:**

```
(1, true)
n=42
```

In `Pair`, `A` and `B` appear in the result type, so building one infers them from the payloads: `Pair(Num(1), Flag(true))` is a `Value[(Int, Bool)]`.

In `Packed`, `A` appears only in the payloads and not in the result. That is an **existential**: the case hides which `A` it holds. Building a `Packed` still fixes `A` (the two payloads must agree, so `Packed(Num(1), f)` with an `f` that takes a `Bool` is an error), but a `when` arm sees `A` as an unknown, fixed type, shown as `A'`. The arm may use `v` and `f` together, since both mention the same `A'`, but it can't treat `A'` as an `Int`.

A lambda whose parameter types aren't written takes them from the case once the other payloads have bound the variable: in `Packed(Num(1), (b) -> if b then "y" else "n")`, `b` is an `Int`, so the `if` is an error.

## More of a GADT

- **Declared case variables, with bounds.** Write a case's own variables in brackets after its name, which allows longer names and interface bounds: `Shown[A Show](v A) Item[String]`. Building one checks the bound, and in its `when` arm `v` is an `A'` that is known to be `Show`, so `v.show()` works and `v.shout()` does not. This is the usual "any showable thing" existential, with the interface named.
- **Methods.** In `impl[T] Value[T]`, `when self` refines `T` the same way a `when` on a parameter does.
- **`is`.** In `if v is Num(n)`, the then-branch knows `T` is `Int`.
- **Header enums.** A header enum (lesson 15) may give its cases result types and payloads. A constant case writes its result type after the header values, `Low(rank: 1) Level[Cold]`. A case with a payload writes the header values first and the payload second, `Num(line: 1)(n Int) Value[Int]`; building it takes only the payload, and the header values are fixed by the case. The header fields are on every case (`v.line`), and a positional pattern (`Num(n)`) sees the payload only.

```moxie
enum Value[T](line Int)
  Num(line: 1)(n Int) Value[Int]
  Flag(line: 2)(b Bool) Value[Bool]
  Add(line: 3)(a Value[Int], b Value[Int]) Value[Int]

fn eval[T](v Value[T]) T = when v
  Num(n) -> n
  Flag(b) -> b
  Add(a, b) -> eval(a) + eval(b)

println(eval(Add(Num(1), Num(2))))
println(Flag(true).line)
```
**Output:**

```
3
2
```

## Which of the three?

Use **tagless final** (lesson 49) when you only run the program and never look inside it. Use **open data types** (lesson 50) when you need to inspect and rewrite the data and also add cases without editing existing code. Use a **GADT** when the set of cases is fixed, you want one closed `when`, and you want the type to rule out ill-typed combinations. A GADT is closed like any enum: a new case means editing the enum.

Haskell and Scala 3 have GADTs with a general type-equality solver, so a case may refine several parameters at once and a pattern match can introduce new type variables. Kotlin and Rust have no GADTs; the usual workaround is a sealed class or enum with an unchecked cast in each arm, which the compiler can't verify. Moxie's version is smaller: a case's result type names each parameter either as a plain type or as the enum's own parameter, and a `when` arm records one equation per parameter.

## Typestate: a type that remembers what happened

A generic type may have a parameter that no field uses. It exists only so the type can say which state a value is in. The state types are empty tuples:

```moxie
tuple Open()
tuple Closed()
tuple File[S]
  name String

fn mk(n String) File[Open] = File(name: n)
fn rd(f File[Open]) String = "read " + f.name
fn cl(f File[Open]) File[Closed] = File(name: f.name)

f = mk("a.txt")
println(rd(f))
g = cl(f)
println(g.name)
```
**Output:**

```
read a.txt
a.txt
```

Now `rd(g)` is a compile error, and so is closing `g` a second time:

```moxie
tuple Open()
tuple Closed()
tuple File[S]
  name String

fn mk(n String) File[Open] = File(name: n)
fn rd(f File[Open]) String = "read " + f.name
fn cl(f File[Open]) File[Closed] = File(name: f.name)

g = cl(mk("a.txt"))
println(rd(g))
```
**The compiler says:**

```
error: mismatched types: expected `File[Open]`, found `File[Closed]`
```

The state costs nothing at run time. Use typestate for protocols with an order: open, then read, then close; connect, then authenticate, then query. A GADT is the tool when the cases of one enum carry different states; typestate is simpler when each state is its own function signature.

## What to remember

- A GADT case states its own result type: `Num(n Int) Value[Int]`.
- A `when` arm learns the case's equations about `T`; impossible cases drop out.
- A case variable that appears only in the payloads is an existential, shown as `A'` inside the arm.
- Typestate: an unused type parameter naming the state; each function's signature says which states it takes and gives.

---

[← Programs with effects as data: the freer monad](42-freer-monad.html) · [Contents](./) · [Reader, writer, and continuations →](62-reader-writer-continuations.html)
