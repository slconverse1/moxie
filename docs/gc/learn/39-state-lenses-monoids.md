---
layout: default
dialect: gc
learn: true
title: "State, lenses, lazy sequences, and monoids · Mixer’s Guide moxie/gc"
---
# 48. State, lenses, lazy sequences, and monoids

<div class='specref' markdown='1'>In the Spec: [23. Functional programming support](../spec.html#s23)</div>

This lesson collects four ideas that functional programmers reach for. In each case moxie offers a plain way to do the job, and sometimes also the classic abstraction.

## State: pass it with `ref`

The recommended way to carry state is `ref` threading, which does the job with the data flow visible at each call:

```moxie
fn push(ref stack List[Int][8], x Int) Unit
  stack += x

fn pop(ref stack List[Int][8]) Int
  top = stack(len(stack) - 1)
  stack = remove_at(stack, len(stack) - 1)
  top

s List[Int][8] = List()
push(ref s, 3)
push(ref s, 4)
a = pop(ref s)
b = pop(ref s)
println("${a * b} ${len(s)}")
```
**Output:**

```
12 0
```

Each call returns a value and hands back the updated state: the `(A, S)` pair of a state monad, without the machinery.

### A State monad, if you want one

A real **State monad** can be defined as a local value, because a closure inside a generic type is specialized per use:

```moxie
tuple State[S, A]
  run (S) -> (A, S)

fn map_state[S, A, B](m State[S, A], f (A) -> B, s S) (B, S)
  (a, s2) = m.run(s)
  (f(a), s2)

fn bind_state[S, A, B](m State[S, A], f (A) -> State[S, B], s S) (B, S)
  (a, s2) = m.run(s)
  f(a).run(s2)

impl[S] Monad[State[S, _]]
  fn fmap[A, B](self State[S, A], f (A) -> B) State[S, B]
    State(run: (s) -> map_state(self, f, s))
  static fn pure[A](a A) State[S, A]
    State(run: (s) -> (a, s))
  fn flat_map[A, B](self State[S, A], f (A) -> State[S, B]) State[S, B]
    State(run: (s) -> bind_state(self, f, s))
  fn ap[A, B](self State[S, (A) -> B], x State[S, A]) State[S, B]
    self.flat_map((g) -> x.fmap(g))

next_id = State(run: (c Int) -> (c + 1, c + 1))
two = next_id.flat_map((a) -> next_id.map((b) -> (a, b)))
r = two.run(0)
println("${r(0)(0)} ${r(0)(1)} ${r(1)}")
```
**Output:**

```
1 2 2
```

The limits are the closure rules: one closure type per composition, no branches that return different closures, no loops or recursion over run-time-length data, and the value is local and transient (it can't go in a `Dict`, atom, or channel). That is why it's an example in a lesson and not a library type, and why `ref` threading is the recommended way.

### Reader and Writer

A **Reader**, a value that many functions read, is a `using` parameter, which the caller can override:

```moxie
fn price(base Int, using tax Int) Int
  base + base * tax / 100

using tax = 20
println("${price(100, using)} ${price(100, 5)}")
```
**Output:**

```
120 105
```

A **Writer** is a function that returns the value together with its log, `(Int, List[String][8])`, and the caller combines the logs with `+`:

```moxie
fn double(x Int) (Int, List[String][8])
  (x * 2, List("doubled ${x}"))

fn inc(x Int) (Int, List[String][8])
  (x + 1, List("incremented ${x}"))

(a, log1) = double(5)
(b, log2) = inc(a)
println(b)
println(log1 + log2)
```
**Output:**

```
11
List("doubled 5", "incremented 10")
```

## Lazy and infinite sequences

Streams are recipes, so an infinite source costs nothing until a terminal runs it:

```moxie
total = 1.. step 1
  |> filter(_ % 3 == 0)
  |> map((n) -> n * n)
  |> take(4)
  |> sum()
under_50 = 1.. step 1 |> map((n) -> n * n) |> take_while(_ < 50) |> count()
println("${total} ${under_50}")
```
**Output:**

```
270 7
```

The first is 9 + 36 + 81 + 144; the second counts the squares 1, 4, 9, 16, 25, 36, and 49. `unfold` builds a generator from a seed, and a `lazy` parameter delays an argument and re-runs it on every read, so call by need is a one-line `once = x`. Nothing is cached for you, so work that is shared needs a recipe you write yourself.

## Lenses: data paths

A data path (lesson 21) is an ordinary function, so paths compose, pass, and combine with `modify`:

```moxie
tuple Firm deriving show
  name String
  floor Int

tuple User deriving show
  id Int
  firm Firm

a = User(id: 1, firm: Firm(name: "Initech", floor: 2))
moved = modify(a, /User/firm/floor, _ + 1)
name_of = /User/firm ~> /Firm/name
println("${(/User/firm/floor)(moved)} ${name_of(moved)}")
println(a)
```
**Output:**

```
3 Initech
User(id: 1, firm: Firm(name: "Initech", floor: 2))
```

`replace` and `modify` rebuild the nested tuples, and `a` is unchanged. In-place update applies when the old value is dead.

## Semigroup and Monoid

A **Semigroup** is a type with an *associative* way to combine two values (`fn combine(self, other Self) Self`). A **Monoid** is a semigroup that also has an identity value (`static fn empty() Self`), such as `""` for text or `List()` for lists. Both are declared in the prelude.

`String` and `List[T]` implement both, with `+` as `combine`. A number has more than one monoid (add with 0, or multiply with 1), so it has none of its own: you pick one by wrapping it. The prelude has small wrapper tuples with one field, `value`:

- `Sum[T]` for anything addable, and `Product[T]` for anything numeric;
- `All` and `Any` for `Bool`, with `and` and `or`;
- `Min[T]` and `Max[T]` for anything ordered; these are only semigroups, since they have no identity.

`fold_all(xs)` combines a stream or list of monoid values (Haskell's `mconcat`), and `fold_map(f, xs)` maps each item to a monoid value first (`foldMap`):

```moxie
println(fold_all(List("a", "b", "c")))
println(fold_all(List(List(1), List(2, 3))))
println(fold_all(List(Sum(1), Sum(2), Sum(3))))
println(fold_map((w) -> List(len(w)), List("a", "bb", "ccc")))
println(fold_map((n) -> Min(n), List(4, 2, 8)))
```
**Output:**

```
abc
List(1, 2, 3)
Sum(value: 6)
List(1, 2, 3)
Min(value: 2)
```

Your own types join with an `impl`, and nothing needs importing:

```moxie
tuple Stats deriving show
  count Int
  total Int

impl Semigroup for Stats
  fn combine(self, other Stats) Stats
    Stats(count: self.count + other.count, total: self.total + other.total)

impl Monoid for Stats
  static fn empty() Stats = Stats(count: 0, total: 0)

println(fold_map((n) -> Stats(count: 1, total: n), List(4, 6, 8)))
println(fold_all[Stats](List()))
```
**Output:**

```
Stats(count: 3, total: 18)
Stats(count: 0, total: 0)
```

An empty input gives `empty()`, so name the type when nothing else says which one: `fold_all[Stats](List())`.

`Dict` and `Set` have no instance, because a merge has to say which side wins and whether a full collection refuses; use `union`, `merge`, and `merge_with`, or write the `impl` you mean for your own wrapper. `a.combine(b)` is the only spelling: there's no operator for it, since `+` already covers strings and lists, and `Addable` covers numbers.

## What moxie leaves out, on purpose

- **Stored capturing closures.** A capturing closure can't live in a concrete tuple field, `Dict`, or channel, so a State value is a transient local, and plain functions are what you store.
- **An IO monad.** Effects are inferred, and the compiler enforces them where they matter (`swap`, `debug_assert`, compile-time evaluation).
- **Hidden laziness and memoization.** Laziness is `lazy` and streams; nothing is cached automatically.
- **Checked monad laws.** The interfaces are conventions, as in Haskell.

## What to remember

- Carry state with `ref` parameters; a State monad is possible but local.
- A Reader is a `using` parameter; a Writer is a function returning `(value, log)`.
- Streams are lazy recipes; an infinite source is fine until a terminal runs it.
- Data paths compose with `~>` and update with `replace` and `modify`.
- `Sum`, `Min`, and friends pick a monoid for numbers; `fold_all` and `fold_map` combine.

---

[← `for` comprehensions](38-for-comprehensions.html) · [Contents](./) · [Tagless final: one program, many interpreters →](40-tagless-final.html)
