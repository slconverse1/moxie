---
layout: default
dialect: gc
learn: true
title: "Methods and interfaces · Learning Guide moxie/gc"
---
<p><small>Data</small></p>

# 24. Methods and interfaces

You have seen methods already (`s.area()`, `xs.map(...)`). This lesson is about declaring them for your own types, and about *interfaces*, which let one function work with many different types as long as they can do the same thing.

## Methods live in impl blocks

A method is a function attached to a type. It is declared inside an `impl` block for that type, and inside it `self` is the value, and the type's fields are in scope by their bare names:

```moxie
tuple Rect(w Double, h Double)
impl Rect
  fn area() Double
    w * h
  fn scaled(k Double) Rect
    Self(w: w * k, h: h * k)
r = Rect(3.0, 4.0)
println(r.area())
println(r.scaled(2.0).area())
```
**Output:**

```
12.0
48.0
```

`Self` is the type the block is for, so `Self(...)` builds another one. A method takes no `self` parameter in its signature; it is implied. All methods live in `impl` blocks, never loose in the file. A method is just a function, and `r.area()` is a shorter way to write the function call `area(r)`.

## Keeping the other fields

A *spread* inside `Self(...)` keeps the other fields, so a method can change one field without listing the rest:

```moxie
tuple Counter(count Int, label String) deriving show
impl Counter
  fn incremented() Counter
    Self(..., count: count + 1)
c = Counter(0, "hits")
println(c.incremented())
println(c.incremented().incremented())
```
**Output:**

```
Counter(count: 1, label: "hits")
Counter(count: 2, label: "hits")
```

## Interfaces: what a type can do

An interface lists methods without bodies. A type satisfies it by writing an `impl` of the interface for that type:

```moxie
interface Speaker
  fn speak() String
tuple Dog(name String)
tuple Robot(serial Int)
impl Speaker for Dog
  fn speak() String
    "Woof! My name is $name"
impl Speaker for Robot
  fn speak() String
    "Beep. Serial $serial"
fn make_them_speak(item Speaker) Unit
  println(item.speak())
make_them_speak(Dog("Rover"))
make_them_speak(Robot(101))
```
**Output:**

```
Woof! My name is Rover
Beep. Serial 101
```

`make_them_speak` takes *anything* that is a `Speaker`. A `Dog` and a `Robot` have nothing else in common, and the function doesn't need them to. A type becomes a `Speaker` by having an `impl` of the interface, which makes "can do X" an explicit promise rather than an accident of naming.

## Generic functions with a bound

The same idea written as a generic function: `[T Speaker]` says "any type `T` that is a `Speaker`". It is better than the form above when two arguments must be the *same* type, or the result is the argument's own type. And it is checked when the program is compiled:

```moxie
interface Speaker
  fn speak() String
tuple Dog(name String)
impl Speaker for Dog
  fn speak() String
    "Woof, $name"
fn twice[T Speaker](a T, b T) String
  a.speak() + " / " + b.speak()
println(twice(Dog("Rex"), Dog("Fido")))
```
**Output:**

```
Woof, Rex / Woof, Fido
```

Passing something that isn't a `Speaker` is a compile error:

```moxie
interface Speaker
  fn speak() String
fn say[T Speaker](item T) Unit
  println(item.speak())
say(42)
```
**The compiler says:**

```
error: `Int` doesn't implement `Speaker`, which `say` requires of `T`
```

The bounds `Equatable`, `Ordered`, `Hashable`, `Show`, `Read`, `Addable`, and `Numeric` are interfaces in the prelude. Your own types satisfy them with `deriving` or with an `impl`, and your own interfaces work in exactly the same way.

## Mixing types in one collection

A `List` or `Array` holds one type. To put a `Dog` and a `Robot` in the same one, name a union of them. The shared call needs no `when`, because every member of the union has it:

```moxie
interface Speaker
  fn speak() String
tuple Dog(name String)
tuple Robot(serial Int)
impl Speaker for Dog
  fn speak() String
    "Woof, $name"
impl Speaker for Robot
  fn speak() String
    "Beep, $serial"
union type Entity = Dog | Robot
crowd Array[Entity] = (Dog("Rex"), Robot(7))
for e in crowd
  println(e.speak())
```
**Output:**

```
Woof, Rex
Beep, 7
```

When the set of types is open-ended, `any Speaker` holds any type that is a `Speaker`, and can be mixed freely.

## Methods that return the type itself

An interface can describe a method that returns the implementing type, which `Self` stands for:

```moxie
interface Resettable
  fn reset() Self
tuple Score(points Int, name String) deriving show
impl Resettable for Score
  fn reset() Score
    Self(..., points: 0)
fn start_over[T Resettable](x T) T
  x.reset()
println(start_over(Score(40, "ann")))
```
**Output:**

```
Score(points: 0, name: "ann")
```

## Changing a variable through its method: ref receivers

A method normally can't change its receiver, since values never change: it returns a new one. When you do want the effect of an in-place update on a name in your program, a `ref` receiver rebinds the caller's variable. The call says `ref` too, which keeps the effect visible:

```moxie
tuple Counter(count Int, label String)
impl Counter
  fn (ref Self) increment() Unit
    count += 1
tally = Counter(0, "hits")
ref tally.increment()
ref tally.increment()
println(tally.count)
```
**Output:**

```
2
```

Leaving off `ref` at the call is an error, the same rule as `ref` parameters.

## Operators are methods too

A type can define operators in its `impl`: the receiver is the left side and the parameter is the right. Defining `<` also gives you `>`, `<=`, and `>=`, and defining `==` gives you `~=`:

```moxie
tuple Money(cents Int) deriving show
impl Money
  fn + (other Money) Money
    Money(cents + other.cents)
  fn < (other Money) Bool
    cents < other.cents
a = Money(150)
b = Money(250)
println(a + b)
println(a < b)
println(b >= a)
```
**Output:**

```
Money(cents: 400)
true
true
```

## Extending a type you don't own

You can't edit `Int` or someone else's type, but you can add plain methods to it with an `impl` block. Such an extension adds a method; it doesn't make the type satisfy an interface:

```moxie
impl Int
  fn double() Int
    self * 2
println(21.double())
```
**Output:**

```
42
```

## A method is a function

Because `x.f(y)` is `f(x, y)`, you can use methods in pipelines, pass them as functions, and give a method a second name with an alias (`fn bump = incremented`). The lesson on pipelines shows the payoff.

---

[← Binary patterns, and taking a value apart by its type](51-binary-patterns-and-type-tags.html) · [Contents](./) · [Streams and pipelines →](21-streams-and-pipelines.html)
