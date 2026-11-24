---
layout: default
learn: true
title: "`for` comprehensions · Moxie Mixer’s Guide"
---
# 47. `for` comprehensions

In the Spec: [23. Functional programming support](../spec.html#s23)
{: .specref}

Lesson 46 chained dependent steps with `|>>`. When there are several steps, the chain gets hard to read, and a `for` block does the same job in a shape that reads top to bottom. A `for` block is a chain of *generators* ending in `yield`, and it works for any type that has a `Monad` instance: `Result`, `List`, `Stream`, and your own types.

## The block form

Each line `name in container` takes the value out of a container, and `yield` builds the final result. A failure (`Empty`, an `Err`) stops the whole block:

```moxie
enum Box[T]
  Full(v T)
  Empty

fn half(n Int) Box[Int]
  if n % 2 == 0 then Box.Full(n / 2) else Box.Empty

impl Monad[Box]
  fn fmap[A, B](self Box[A], f (A) -> B) Box[B]
    when self
      Full(v) -> Box.Full(f(v))
      Empty -> Box.Empty
  static fn pure[A](a A) Box[A]
    Box.Full(a)
  fn ap[A, B](self Box[(A) -> B], x Box[A]) Box[B]
    when self
      Full(g) -> x.fmap(g)
      Empty -> Box.Empty
  fn flat_map[A, B](self Box[A], f (A) -> Box[B]) Box[B]
    when self
      Full(v) -> f(v)
      Empty -> Box.Empty

good = for
  a in Box.Full(20)
  b in half(a)
  c in half(b)
  yield a + c
bad = for
  a in Box.Full(10)
  b in half(a)
  c in half(b)
  yield a + c
println(good)
println(bad)
```
**Output:**

```
Box.Full(25)
Box.Empty
```

20 halves to 10 and then to 5, so `good` is `Box.Full(25)`. 10 halves to 5, and 5 is odd, so `bad` is `Box.Empty`. The block turns into `flat_map` and `map` calls through the type's `Monad` instance.

Inside the block, three kinds of line are allowed:

- `name in expr` takes a value out of a container;
- `name = expr` binds a plain value, with no container;
- a **refutable** binding, `Active(_, rank) = user else Err(...)`, takes a value apart and gives a failure when the pattern doesn't fit (lesson 22's let-else).

## An example: paying people

Here is a small payroll, written three ways. First the data and the lookup:

```moxie
enum Rank
  Manager,
  Staff

enum User
  Active(name String, rank Rank),
  Retired(name String)

enum PayError deriving show
  NotFound(id Int)

fn find_user(id Int) Result[User, PayError]
  when id
    42 -> Ok(User.Active(name: "Ada", rank: Manager))
    7 -> Ok(User.Active(name: "Bo", rank: Staff))
    9 -> Ok(User.Retired(name: "Cy"))
    else Err(NotFound(id: id))

fn base_pay(rank Rank) Int
  when rank
    Manager -> 500000
    Staff -> 300000

fn pay_one(id Int, bonus_pct Int) Result[Int, PayError]
  user = find_user(id)?
  Active(_, rank) = user else Err(NotFound(id: id))
  base = base_pay(rank)
  cents = if bonus_pct > 0 then base + base * bonus_pct / 100 else base
  Ok(cents)

fn pay_for(id Int, bonus_pct Int) Result[Int, PayError]
  for
    user in find_user(id)
    Active(_, rank) = user else Err(NotFound(id: id))
    base = base_pay(rank)
    yield base + base * bonus_pct / 100

fn process_batch(ids List[Int][8], bonus_pct Int) Result[List[Int][8], PayError]
  ids |> traverse(pay_one(_, bonus_pct))

println("${pay_one(42, 10)} ${pay_for(42, 10)}")
when process_batch(List(42, 7), 10)
  Ok(all) -> println("${all(0)} ${all(1)}")
  Err(e) -> println("${e}")
when process_batch(List(42, 9), 10)
  Ok(all) -> println("${all(0)}")
  Err(e) -> println("${e}")
```
**Output:**

```
Ok(550000) Ok(550000)
550000 330000
PayError.NotFound(9)
```

`pay_one` uses `?`, `pay_for` uses `for`, and `process_batch` runs the first over a list with `traverse`. The three results agree. In the batch, the first error wins: the retired user `9` isn't `Active`, so the batch stops with `NotFound(9)`.

An error that carries run-time text must be a typed payload such as `NotFound(id: id)`, since a static-string `Error` can't hold it.

Guards are ordinary functions from the prelude: `ensure(cond, err)` for `Result`, `guard(cond)` for a plain condition (`Ok(())`, or an `Err` with the code `MISSING`), and `or_else` to recover from a failure.

## Independent generators: `and`

When the generators don't depend on each other, join them with a leading `and`. The block then compiles through `ap` instead of `flat_map`, so it needs only an `Applicative`:

```moxie
fn both(a Result[Int, Error], b Result[Int, Error]) Result[Int, Error]
  for
    x in a
    and y in b
    yield x + y

println(both(Ok(1), Ok(2)))
```
**Output:**

```
Ok(3)
```

## Comprehensions that build a collection

A one-line `for` inside `List(...)`, `Set(...)`, or `Dict(...)` builds a collection. It takes one generator and, optionally, one filter; the collection's size comes from its declared type:

```moxie
xs = List(1, 2, 3, 4)
squares List[Int][8] = List(x * x for x in xs if x > 1)
words = List("ab", "cde")
lens Dict[String, Int][8] = Dict(w -> len(w) for w in words)
println("${len(squares)} ${squares(0)} ${lens("cde")}")
```
**Output:**

```
3 4 Ok(3)
```

The squares are 4, 9, and 16, so there are three of them and the first is 4. A `Dict` lookup returns a `Result`, which is why `lens(cde)` prints as `Ok(3)`.

For more than one generator, use the block form with `yield`, which is the general tool. Left out on purpose: custom builders, `try`/`with`, `use!`, and loops inside the block. Nested generators over streams work through `Monad[Stream]`, and the result is a view, so it can't be returned from a function.

## What to remember

- A block of generators ending in `yield` is `flat_map` and `map` underneath; a failure stops it.
- `name = expr` binds a plain value; a pattern with `else` is a let-else.
- A leading `and` joins independent generators, needing only `Applicative`.
- `List(x for x in xs if cond)` builds a collection in one line; its size comes from the declared type.
- Choose `?` for a short function, `for` when you have a chain of steps and the shape reads better, `traverse` for a list.

---

[← Mapping, sequencing, and combining: functors, applicatives, and monads](37-functors-and-monads.html) · [Contents](./) · [State, lenses, lazy sequences, and monoids →](39-state-lenses-monoids.html)
