---
layout: default
title: "Tagless final: one program, many interpreters · Learn moxie"
---
<p><small>Functional programming</small></p>

# 48. Tagless final: one program, many interpreters

Suppose you are writing a tiny language of sums (numbers, `+`, negation) and want to run it, print it, and later do more with it. The usual way is a data type (an `enum`) and one function per job that takes it apart with `when`. **Tagless final** turns that around: you write the language as an *interface*, and a program in it is a generic function that builds its result using the interface's functions. An interpreter is a type that implements the interface, so choosing the interpreter is choosing a type argument, and no tree is built at all.

This is an advanced lesson. It uses interfaces (lesson 20) and generics (lesson 11) together, and it shows that a language with no macros can still describe a program once and run it in many ways.

## One program, two interpreters

```moxie
interface Expr
  static fn lit(n Int) Self,
  static fn add(a Self, b Self) Self,
  static fn neg(a Self) Self

fn example[R Expr]() R
  R.add(R.lit(8), R.neg(R.add(R.lit(1), R.lit(2))))

tuple Eval
  value Int
tuple Pretty
  text String

impl Expr for Eval
  static fn lit(n Int) Eval
    Eval(value: n)
  static fn add(a Eval, b Eval) Eval
    Eval(value: a.value + b.value)
  static fn neg(a Eval) Eval
    Eval(value: 0 - a.value)

impl Expr for Pretty
  static fn lit(n Int) Pretty
    Pretty(text: "${n}")
  static fn add(a Pretty, b Pretty) Pretty
    Pretty(text: "(${a.text} + ${b.text})")
  static fn neg(a Pretty) Pretty
    Pretty(text: "-${a.text}")

println(example[Eval]().value)
println(example[Pretty]().text)
```
**Output:**

```
5
(8 + -(1 + 2))
```

`example` never says which interpreter it uses: `R` stands for the type that will hold the result, and `R.lit(8)` calls `lit` of whatever `R` is. The members are `static` because a `lit` has no value of the type to be called on yet. The result type is `Self`, so `add` takes two of its own results.

The first interpreter computes: 8 minus (1 + 2) is 5. The second prints the program as text.

## A new operation, with the old code untouched

With a data type, adding multiplication means editing the `enum` and every `when` over it. Here you add a second interface, and a program that needs both asks for both with `+`:

```moxie
interface Expr
  static fn lit(n Int) Self,
  static fn add(a Self, b Self) Self

interface Mul
  static fn mul(a Self, b Self) Self

fn sum_sq[R Expr + Mul](x R) R
  R.add(R.mul(x, x), R.lit(1))

tuple Eval
  value Int
impl Expr for Eval
  static fn lit(n Int) Eval
    Eval(value: n)
  static fn add(a Eval, b Eval) Eval
    Eval(value: a.value + b.value)
impl Mul for Eval
  static fn mul(a Eval, b Eval) Eval
    Eval(value: a.value * b.value)

tuple Pretty
  text String
impl Expr for Pretty
  static fn lit(n Int) Pretty
    Pretty(text: "${n}")
  static fn add(a Pretty, b Pretty) Pretty
    Pretty(text: "(${a.text} + ${b.text})")
impl Mul for Pretty
  static fn mul(a Pretty, b Pretty) Pretty
    Pretty(text: "${a.text} * ${b.text}")

println(sum_sq(Eval(value: 3)).value)
println(sum_sq(Pretty(text: "x")).text)
```
**Output:**

```
10
(x * x + 1)
```

Programs that only use `Expr` still compile and run against `Eval` and `Pretty` exactly as before, and a type that has only `Expr` simply can't run `sum_sq`: the compiler says it doesn't implement `Mul`.

## Two interpreters at once

A pair of interpreters is itself an interpreter, so one run can compute the value and the text together:

```moxie
interface Expr
  static fn lit(n Int) Self,
  static fn add(a Self, b Self) Self

fn total[R Expr](a Int, b Int) R
  R.add(R.lit(a), R.lit(b))

tuple Eval
  value Int
tuple Pretty
  text String
impl Expr for Eval
  static fn lit(n Int) Eval
    Eval(value: n)
  static fn add(a Eval, b Eval) Eval
    Eval(value: a.value + b.value)
impl Expr for Pretty
  static fn lit(n Int) Pretty
    Pretty(text: "${n}")
  static fn add(a Pretty, b Pretty) Pretty
    Pretty(text: "(${a.text} + ${b.text})")

tuple Both[A, B]
  first A
  second B
impl[A Expr, B Expr] Expr for Both[A, B]
  static fn lit(n Int) Both[A, B]
    Both(first: A.lit(n), second: B.lit(n))
  static fn add(a Both[A, B], b Both[A, B]) Both[A, B]
    Both(first: A.add(a.first, b.first), second: B.add(a.second, b.second))

r = total[Both[Eval, Pretty]](4, 5)
println("${r.second.text} = ${r.first.value}")
```
**Output:**

```
(4 + 5) = 9
```

Name the pair type when you call (`total[Both[Eval, Pretty]]`): a result type is the only thing that says which `lit` to call, so there is nothing else to infer it from.

## Keeping the types straight

The language above has one kind of value. When it has two (numbers and booleans, with `if` and `<=`), the interface has to say which is which, or `add(lit(1), bool(true))` would be meaningless. Make the representation a type constructor, as in the constructor interfaces of lesson 37 (`R[_]`), and give each operation a precise type:

```moxie
interface Sym[R[_]]
  static fn lit(n Int) R[Int],
  static fn bool(b Bool) R[Bool],
  static fn add(a R[Int], b R[Int]) R[Int],
  static fn leq(a R[Int], b R[Int]) R[Bool],
  static fn cond[A](c R[Bool], t R[A], e R[A]) R[A]

tuple Id[A]
  value A
tuple Show[A]
  text String

fn prog[R[_] Sym]() R[Int]
  R.cond(R.leq(R.lit(1), R.lit(2)), R.add(R.lit(10), R.lit(5)), R.lit(0))

impl Sym[Id]
  static fn lit(n Int) Id[Int]
    Id(value: n)
  static fn bool(b Bool) Id[Bool]
    Id(value: b)
  static fn add(a Id[Int], b Id[Int]) Id[Int]
    Id(value: a.value + b.value)
  static fn leq(a Id[Int], b Id[Int]) Id[Bool]
    Id(value: a.value <= b.value)
  static fn cond[A](c Id[Bool], t Id[A], e Id[A]) Id[A]
    if c.value then t else e
impl Sym[Show]
  static fn lit(n Int) Show[Int]
    Show(text: "${n}")
  static fn bool(b Bool) Show[Bool]
    Show(text: "${b}")
  static fn add(a Show[Int], b Show[Int]) Show[Int]
    Show(text: "(${a.text} + ${b.text})")
  static fn leq(a Show[Int], b Show[Int]) Show[Bool]
    Show(text: "(${a.text} <= ${b.text})")
  static fn cond[A](c Show[Bool], t Show[A], e Show[A]) Show[A]
    Show(text: "if ${c.text} then ${t.text} else ${e.text}")

println(prog[Id]().value)
println(prog[Show]().text)
```
**Output:**

```
15
if (1 <= 2) then (10 + 5) else 0
```

`cond` takes a `R[Bool]` for its test and two `R[A]` for its branches, so every interpreter has to give a boolean test and branches of one type, and each `impl` is checked against those signatures. A typed evaluator over a data type needs GADTs for this (a case that states its own result type, lesson 42); in the tagless style the interface carries the types.

The body of a generic program is checked against those signatures too: `R.add(R.lit(1), R.bool(true))` is a compile error, and so is a number as the test of `cond`.

## Back to data, and the way home

The two styles are the same information. A data type is just one more interpreter, the one that builds a tree, and any tree can be run through any interpreter by walking it:

```moxie
interface Expr
  static fn lit(n Int) Self,
  static fn add(a Self, b Self) Self,
  static fn neg(a Self) Self

enum Tree deriving show
  Lit(n Int)
  Add(a Tree, b Tree)
  Neg(a Tree)

impl Expr for Tree
  static fn lit(n Int) Tree
    Tree.Lit(n)
  static fn add(a Tree, b Tree) Tree
    Tree.Add(a, b)
  static fn neg(a Tree) Tree
    Tree.Neg(a)

fn interpret[R Expr](t Tree) R
  when t
    Lit(n) -> R.lit(n)
    Add(a, b) -> R.add(interpret[R](a), interpret[R](b))
    Neg(a) -> R.neg(interpret[R](a))

fn example[R Expr]() R
  R.add(R.lit(8), R.neg(R.add(R.lit(1), R.lit(2))))

tuple Eval
  value Int
impl Expr for Eval
  static fn lit(n Int) Eval
    Eval(value: n)
  static fn add(a Eval, b Eval) Eval
    Eval(value: a.value + b.value)
  static fn neg(a Eval) Eval
    Eval(value: 0 - a.value)

t = example[Tree]()
println(t)
println(interpret[Eval](t).value)
```
**Output:**

```
Tree.Add(Tree.Lit(8), Tree.Neg(Tree.Add(Tree.Lit(1), Tree.Lit(2))))
5
```

Reach for the tree when the program has to be inspected, stored, or rewritten (an optimizer needs to look at the shape), and for tagless final when you only run it, or when you want to add operations and interpreters without touching each other.

## Mistakes

- Leaving `static` off the operations: a `lit` with no `self` can't be called on a result.
- Calling `example()` without naming the interpreter. Write `example[Eval]()`: nothing else says which type `R` is.
- Passing a type that lacks `impl Expr` or `impl Mul` to a program that needs it. That one is a compile error.

## What to remember

- The language is an interface; a program is a generic function over `R`; an interpreter is a type with an `impl`.
- Add operations with new interfaces and combine them with `+`; old programs keep working.
- A pair `Both[A, B]` is an interpreter that runs two at once.
- For languages with several kinds of value, make the interface over a type constructor `R[_]`.
- A tree (`enum`) is one more interpreter, and `interpret` runs it through any other.

---

[← State, lenses, lazy sequences, and monoids](39-state-lenses-monoids.html) · [Contents](./) · [Data types that grow: the expression problem →](41-open-data-types.html)
