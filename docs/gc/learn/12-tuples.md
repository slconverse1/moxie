---
layout: default
dialect: gc
learn: true
title: "Tuples · Mixer’s Guide moxie/gc"
---
# 14. Tuples

<div class='specref' markdown='1'>In the Spec: [6. Tuples, enums, aliases, unions](../spec.html#s6), [8. Patterns and `when`](../spec.html#s8)</div>

A *tuple* groups a few values into one. It is moxie's way of making a record: a point is an `x` and a `y`, a user is a name and an age. Tuples hold values of any types, and each field has a name.

## An unnamed tuple

The simplest tuple is a few values in parentheses. You have already met them: `divmod` returned `(Int, Int)`.

```moxie
pair = (3, "three")
println(pair)
println(pair(0))
println(pair(1))
```
**Output:**

```
(3, "three")
3
three
```

A field of a tuple is read by its position in parentheses, starting at 0. A tuple binding takes the whole thing apart:

```moxie
pair = (3, "three")
number, word = pair
println("$number is $word")
```
**Output:**

```
3 is three
```

## Giving the fields names

Positions are easy to mix up. Put names on the fields and the tuple documents itself. Such a tuple needs no declaration; its type is made from what you write:

```moxie
user = (name: "Alice", age: 30)
println(user)
println(user.name)
println(user.age)
println(user(1))
```
**Output:**

```
(name: "Alice", age: 30)
Alice
30
30
```

A named field is read with a dot, or by position as before. Two tuples with the same field names and types are the same type.

## Declaring a tuple type

When you use the same shape in many places, declare it with `tuple`. A declaration gives the type a name and lists its fields, each as a name and a type, with no colons:

```moxie
tuple Point deriving show
  x Double,
  y Double
p = Point(x: 1.5, y: 2.0)
println(p)
println(p.x * 3)
```
**Output:**

```
Point(x: 1.5, y: 2.0)
4.5
```

A short tuple can go on one line, with the fields in parentheses after the name:

```moxie
tuple Point(x Int, y Int) deriving show
p = Point(3, 4)
println(p)
println(p.x + p.y)
```
**Output:**

```
Point(x: 3, y: 4)
7
```

You build a value by writing the type's name and the fields. You can name them, in any order, or give them by position when that is clear.

## Printing and comparing

A declared tuple doesn't print or compare until you ask. `deriving` lists what to generate: `show` (to print), `eq` (to compare with `==`), `ord` (to order with `<`), `hash` (to use as a Dict key or in a Set), and `read` (to parse from text):

```moxie
tuple Product deriving show, eq
  name String,
  price Int
a = Product(name: "Keyboard", price: 120)
b = Product(name: "Keyboard", price: 120)
c = Product(name: "Mouse", price: 25)
println(a)
println(a == b)
println(a == c)
```
**Output:**

```
Product(name: "Keyboard", price: 120)
true
false
```

Comparing declared tuples is checked: without `deriving eq`, `==` on them is a compile error that tells you what to add.

```moxie
tuple Point(x Int, y Int)
println(Point(1, 2) == Point(1, 2))
```
**The compiler says:**

```
error: `==` on `Point` needs `eq`: write `deriving eq` on its declaration (or an `impl Equatable`)
```

Nothing is compared, ordered, or hashed unless the declaration says so, which keeps the meaning of `==` under your control. (The unnamed tuples in the first part of this lesson need no `deriving`: they print and compare by their parts.)

## Changing a tuple: it makes a new one

Tuples are values, so you never change one in place. You make a new tuple that is the old one with some fields different. A *spread*, `...p`, brings in all the old fields, and the fields you write after it replace them:

```moxie
tuple Point(x Int, y Int) deriving show
p = Point(3, 4)
q = Point(...p, y: 9)
println(p)
println(q)
```
**Output:**

```
Point(x: 3, y: 4)
Point(x: 3, y: 9)
```

`p` is unchanged. The `update` form says the same thing and reads well for several changes, because the new values can use the old ones:

```moxie
tuple Account(name String, score Int) deriving show
a = Account("Bob", 150)
b = a.update
  score: a.score + 10
println(b)
```
**Output:**

```
Account(name: "Bob", score: 160)
```

A compound assignment works on a field too: `a.score += 10` means "rebind `a` to a copy with the score raised by ten".

```moxie
tuple Account(name String, score Int) deriving show
a = Account("Bob", 150)
a.score += 10
println(a)
```
**Output:**

```
Account(name: "Bob", score: 160)
```

## Default values

Trailing fields can have defaults, written with `=`. The default must be something the compiler can work out ahead of time, such as a literal. Leave those fields out when you build the value:

```moxie
tuple Options deriving show
  host String = "localhost",
  port Int = 4000,
  retries Int = 3
println(Options())
println(Options(retries: 5))
println(Options(host: "example.com", port: 80))
```
**Output:**

```
Options(host: "localhost", port: 4000, retries: 3)
Options(host: "localhost", port: 4000, retries: 5)
Options(host: "example.com", port: 80, retries: 3)
```

## Tuples as arguments

Tuples are the natural way to pass a bundle of values, and a function can ask only for the fields it needs. A parameter written `(name String, ...)` accepts *any* tuple with at least a `name` field of type `String`, and ignores the rest:

```moxie
tuple Employee
  name String
  age Int
  salary Int
fn greet(who (name String, ...)) String = "hi ${who.name}"
println(greet((name: "Alice", age: 30)))
println(greet(Employee(name: "Bo", age: 40, salary: 9)))
```
**Output:**

```
hi Alice
hi Bo
```

A tuple whose fields don't include what the function asks for is a compile error that names the missing field.

## Taking tuples apart with patterns

A pattern with the type's name takes a tuple apart in a binding, and can name only some of the fields:

```moxie
tuple Point(x Double, y Double)
Point(x, y) = Point(1.5, 2.0)
println("$x $y")
```
**Output:**

```
1.5 2.0
```

The lesson on patterns shows every shape a pattern can take, in `when`, in function parameters, and in `is` tests.

## A tuple holding a resource

A tuple that holds something that must be closed or handed over exactly once, such as a channel end, is itself such a resource. The lessons on resources and concurrency cover that.

---

[← Generic functions](11-generics.html) · [Contents](./) · [Enums →](13-enums.html)
