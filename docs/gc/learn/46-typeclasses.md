---
layout: default
dialect: gc
learn: true
title: "Typeclasses · Mixer’s Guide moxie/gc"
---
# 56. Typeclasses

<div class='specref' markdown='1'>In the Spec: [12. Interfaces and `impl` blocks](../spec.html#s12)</div>

Moxie has no separate typeclass feature. A class is an `interface`, an instance is an `impl`, a constraint is a bound, a superclass is an embedded interface, a member with no receiver is a `static fn`, and deriving is `deriving show, eq, ord, read, hash`. This lesson gathers those pieces in one place. If you know Haskell, the last section is a translation table.

## A class, its instances, and a constrained function

```moxie
interface Semigroup
  fn combine(other Self) Self
interface Monoid
  Semigroup
  static fn empty() Self
impl Monoid for Int
  fn combine(other Int) Int
    self + other
  static fn empty() Int
    0
tuple Max
  value Int
impl Monoid for Max
  fn combine(other Max) Max
    if value > other.value then self else other
  static fn empty() Max
    Max(value: -1000000)
fn mconcat[T Monoid, N](xs Array[T][N]) T
  xs |> reduce(T.empty(), (a, b) -> a.combine(b))
nums Array[Int] = (1, 2, 3)
maxes Array[Max] = (Max(3), Max(9), Max(4))
println("${mconcat(nums)} ${mconcat(maxes).value}")
```
**Output:**

```
6 9
```

The tuple `Max` is built both ways: `Max(value: -1000000)` names the field and `Max(3)` is positional. A constructor is also a function, so `Array(3, 9, 4).fmap(Max)` builds the same array as `maxes`.

`Monoid` embeds `Semigroup`, which is the superclass relationship, and one `impl Monoid` supplies both members. (The prelude already declares `Semigroup` and `Monoid`, lesson 48; this example writes its own so you can see how an interface is built, and a declaration in your program is the one it uses.)

A member with no receiver is a `static fn`, reached through the type, so Haskell's `mempty` is `T.empty()`. The compiler specializes `mconcat` for each type, with no tables at run time.

## Associated types

An interface can name a type that each impl chooses, so there's no need for an extra parameter or functional dependencies:

```moxie
interface Container
  type Item
  fn get(i Int) Result[Item, Error]
  fn size() Int
tuple Names
  items List[String][8]
impl Container for Names
  type Item = String
  fn get(i Int) Result[String, Error]
    get(items, i)
  fn size() Int
    len(items)
fn last_of[C Container](c C) Result[C.Item, Error]
  c.get(c.size() - 1)
names = Names(items: List("ada", "bob"))
when last_of(names)
  Ok(n) -> println(n)
  Err(e) -> println("empty")
```
**Output:**

```
bob
```

A type has exactly one impl of each interface, so `C.Item` is never ambiguous. On an `any Container`, whose concrete type is hidden, `Item` is hidden too: each such value has its own, written `c.Item`. You can unwrap it, print it, pass it back to the same value (`c.put(x)`), or narrow `c` with `is`, but the checker never treats it as an `Int` or a `String`. Write a generic function (`fn f[C Container](c C)`, as `last_of` does) when you need the concrete type.

## Constructor classes

A class over a type constructor takes `F[_]`, and an instance names the constructor itself. (`List` by itself is a type constructor, and a parameter that stands for one is what Haskell and Scala call a higher-kinded type. Without it, `double_in` below would have to be written again for every container.)

With the prelude's `Functor`, `Applicative`, and `Monad` interfaces and an `impl Monad[Box]` (lesson 46), you can write code that works for *any* monad:

```moxie
enum Box[T] deriving show
  Full(v T)
  Empty

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

fn double_in[F[_] Monad](m F[Int]) F[Int]
  m.flat_map((x) -> F.pure(x * 2))
r Result[Int, Error] = Ok(21)
println("${double_in(Box.Full(21))} ${double_in(r)}")
```
**Output:**

```
Box.Full(42) Ok(42)
```

`Box.Full(21)` and `Ok(21)` both work, and each gives back its own kind of container. And an applicative lift:

```moxie
enum Box[T] deriving show
  Full(v T)
  Empty

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

fn add(a Int, b Int) Int = a + b
fn lift2[F[_] Applicative, A, B, C](f (A, B) -> C, a F[A], b F[B]) F[C]
  a.map(curry(f)).ap(b)
none Box[Int] = Box.Empty
print("${lift2(add, Box.Full(2), Box.Full(3))} ")
println("${lift2(add, none, Box.Full(3))}")
```
**Output:**

```
Box.Full(5) Box.Empty
```

Return-type polymorphism needs an explicit type, so write `F.pure(x)` or `Box.pure(x)`; a bare `pure(x)` is not dispatched from context.

## Conditional instances

An `impl` may put a bound on its own type parameters:

```moxie
interface Describable
  fn describe() String
impl Describable for Int
  fn describe() String
    "int $self"
tuple Crate[A]
  value A
impl[A Describable] Describable for Crate[A]
  fn describe() String
    "crate(${self.value.describe()})"
println(Crate(7).describe())
```
**Output:**

```
crate(int 7)
```

`Crate[A]` is `Describable` exactly when `A` is.

## Interface values: `any`

When you need a mixed collection and don't control the set of types, `any Voice` holds one of any type that implements `Voice`:

```moxie
interface Voice
  fn speak() String
tuple Dog
  name String
tuple Robot
  serial Int
impl Voice for Dog
  fn speak() String
    "Woof! My name is ${name}"
impl Voice for Robot
  fn speak() String
    "Beep Boep! Serial count is ${serial}"
crowd = List[any Voice][4](Dog(name: "Rex"), Robot(serial: 7))
for s in crowd
  println(s.speak())
```
**Output:**

```
Woof! My name is Rex
Beep Boep! Serial count is 7
```

A call on an `any` value switches on a tag, so only members with a receiver, and `Self` used only as a result, are callable through it. `any` values aren't comparable or usable as keys unless the interface lists `Equatable`, `Ordered`, or `Hashable` inside it; then `==`, `<`, `Set`, and `Dict` keys all work.

## Default method bodies

A member may have a default body that an `impl` can override:

```moxie
interface Greeter
  fn name() String
  fn greet() String
    "Hello, ${self.name()}"
tuple Pal
  id String
tuple Boss
  title String
impl Greeter for Pal
  fn name() String
    id
impl Greeter for Boss
  fn name() String
    title
  fn greet() String
    "Good day, ${self.name()}"
println("${Pal(id: "ada").greet()} / ${Boss(title: "Chief").greet()}")
```
**Output:**

```
Hello, ada / Good day, Chief
```

The default is specialized for each implementing type.

## Haskell to moxie, at a glance

- `class` and `instance` become `interface` and `impl X for T`; `instance Monad Box` becomes `impl Monad[Box]`.
- Superclasses are embedded interfaces; constraints are bounds like `[T Monoid]`.
- `deriving` is `deriving show, eq, ord, read`.
- Instances must live with the type or the interface (no orphans).
- Default method bodies and associated types exist. Missing from the language: functional dependencies, type families (see the next lesson for type functions), and monad transformers (in GC-free moxie; moxie/gc has them as the library `fp.trans`).

## Mistakes

- An `impl` of someone else's interface for someone else's type.
- Calling `empty()` with no type to say which one.
- Combining two `any Monoid` values (`Self` in a parameter).
- Comparing `any` values with `==` when the interface doesn't list `Equatable`.
- A bound written twice on one parameter (embed the interfaces instead).

## What to remember

- Interface = class, `impl` = instance, bound = constraint, embedded interface = superclass.
- `static fn` members are reached through the type: `T.empty()`.
- `type Item` inside an interface is an associated type.
- `F[_]` stands for a type constructor; write code once for every monad.
- `any Interface` holds a mixed collection when the set of types is open.

---

[← Receiver blocks, interface composition, and mocks](45-receiver-blocks-and-mocks.html) · [Contents](./) · [Types that compute →](47-types-that-compute.html)
