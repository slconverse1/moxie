---
layout: default
learn: true
title: "Modularity and encapsulation without classes · Moxie Mixer’s Guide"
---
# 73. Modularity and encapsulation without classes

Many languages keep code in order with classes: a class groups the functions that work on its data, and its private fields hide the data from the rest of the program. Moxie gets the same two things without classes. A *module* is a file, or a package of files, and `export` says what the rest of the program may use. *Encapsulation* is hiding state, and moxie does it with closures and with opaque types. Lesson 27 covers packages in full, so this lesson shows the ideas on their own.

## A module is a file

Everything in a file is private unless it is marked `export`. The functions marked `export` are the module's interface, and the others are its internal helpers. Other code can only call what the module exports, so the helpers can change without anyone noticing.

```moxie
fn square(x Double) Double
  x * x

export fn area(w Double, h Double) Double
  w * h

export fn diagonal_squared(w Double, h Double) Double
  square(w) + square(h)

println(area(3.0, 4.0))
println(diagonal_squared(3.0, 4.0))
```
**Output:**

```
12.0
25.0
```

`square` is a helper, and `area` and `diagonal_squared` are the interface. Lesson 27 shows how a program imports a module from another file, and how `import` selects names.

## Hiding state in a closure

A closure remembers the variables it was made with, and nothing outside can reach them except through the function it returns. So a function can keep a private counter, with no field and no object:

```moxie
fn make_counter() () -> Int
  hits = Atom[Int](0)
  bump = fn () Int
    swap(hits, (n) -> n + 1)
  bump

next = make_counter()
println(next())
println(next())
other = make_counter()
println(other())
println(next())
```
**Output:**

```
1
2
1
3
```

Each call to `make_counter` makes its own `hits`. The two counters don't share state, and the code outside can't read or change `hits` except by calling the function it was given. An `Atom` is used so the count is changed in one step; lesson 24 covers atoms.

## Hiding a representation with an opaque type

An opaque type hides what it is made of. Outside the file that declares it, you can name the type and hold it, but you can't build it or read its fields. So the only way to get one is through functions that check the rules. Here an account can't go negative, because every change goes through `open_account` and `deposit`:

```moxie
tuple AccountData
  balance Double

opaque type Account = AccountData

export fn open_account(initial Double) Result[Account, Error]
  if initial < 0.0
    return Err(Error("opening balance can't be negative"))
  Ok(Account(AccountData(initial)))

export fn deposit(a Account, amount Double) Account
  if amount > 0.0
    return Account(AccountData(cast[AccountData](a).balance + amount))
  a

export fn balance(a Account) Double
  cast[AccountData](a).balance

when open_account(10.0)
  Err(e) -> println("no account")
  Ok(a) -> println(balance(deposit(a, 5.0)))
```
**Output:**

```
15.0
```

Lesson 18 explains opaque types, and why they cost nothing at run time. Inside the file that declares `Account`, the representation is still visible, which is why `deposit` can see the balance. Outside, only the exported functions are available.

## Why this is enough

A module with exported functions and private helpers gives you the boundary a class would. A closure with private state gives you an object's private field. An opaque type gives you a type whose invariant can't be broken from outside. Moxie doesn't need classes to get any of these.

## What to remember

- A file is a module, and `export` marks its interface.
- A closure holds private state that only the functions it returns can reach.
- An opaque type hides its representation, so its rules can't be broken from outside.
- Lesson 27 covers packages of several files, and lesson 18 covers opaque types in full.

---

[← Existential types](73-existential-types.html) · [Contents](./) · [Unifying tuples and parameter lists →](75-unifying-tuples-and-parameters.html)
