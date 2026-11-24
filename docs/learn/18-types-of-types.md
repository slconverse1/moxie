---
layout: default
learn: true
title: "Naming types: aliases, opaque types, and unions · Moxie Mixer’s Guide"
---
# 21. Naming types: aliases, opaque types, and unions

In the Spec: [6. Tuples, enums, aliases, unions](../spec.html#s6)
{: .specref}

So far each type has been either built in or declared as a tuple or enum. This lesson covers three more ways to shape types: giving an existing type a second name, making a genuinely new type from an old one, and describing a value that can be one of several types.

## Type aliases

An alias gives a type another name. It is the same type, so the two can be used interchangeably:

```moxie
type Meters = Double
fn half(m Meters) Meters = m / 2.0
distance Double = 100.0
println(half(distance))
```
**Output:**

```
50.0
```

An alias helps a reader (`Meters` says more than `Double`) and shortens long types. It adds no protection: a `Double` goes wherever a `Meters` is expected. An alias can't have `deriving` or default values for that reason, since it isn't a new thing.

## Opaque types: genuinely new

`opaque type` makes a new type that is built from an old one but can't be mixed up with it. The only way in is the type's own constructor:

```moxie
opaque type Meters = Double
opaque type Feet = Double
fn to_feet(m Meters) Feet
  Feet(cast[Double](m) * 3.28084)
println(to_feet(Meters(100.0)))
```
**Output:**

```
328.084
```

A `Meters` and a `Feet` are different types, even though both are doubles underneath, so passing one where the other is wanted is a compile error:

```moxie
opaque type Meters = Double
opaque type Feet = Double
fn describe(m Meters) String = "a distance"
println(describe(Feet(1.0)))
```
**The compiler says:**

```
error: mismatched types: expected `Meters`, found `Feet`
```

Opaque types prevent the classic mistake of passing a user id where an order id was expected, or metres where feet were. They cost nothing at run time. (Inside the file that declares one, it is still a double underneath; the representation is hidden from other packages.)

## Generic tuples

A tuple can take type parameters, like a function can. The compiler infers them from the fields:

```moxie
tuple Container[T]
  item T
a = Container(item: 5.59)
b = Container(item: "hello")
println("${a.item} ${b.item}")
```
**Output:**

```
5.59 hello
```

## Union types: one of several

A union type says a value is one of a list of types. It is written with `|`, and the type name is declared with `union type`:

```moxie
union type Identifier = Int | String
fn describe(id Identifier) String
  when id
    Int -> "numeric id $id"
    String -> "text id $id"
println(describe(42))
println(describe("Node-04"))
```
**Output:**

```
numeric id 42
text id Node-04
```

A value of either member converts into the union implicitly. To use it, take it apart with `when`: an arm names a *type* instead of a value, and `when` must cover every member.

A union differs from an enum in what the cases are. An enum's cases are new names that you declare. A union's members are types that already exist.

## Checking which member it is: is

A value of a union is one of its members, and the compiler holds you to that. `id + 1` on an `Identifier` is an error, because it might be a `String`. Say which member it is first. A `when` does that, and so does `is`. After the test, the compiler *knows* the type inside the branch:

```moxie
union type Identifier = Int | String
fn weight(id Identifier) Int
  if id is Int
    id + 1
  elif id is String
    len(id)
  else
    0
println(weight(41))
println(weight("Node-04"))
```
**Output:**

```
42
7
```

Inside the first branch `id` is an `Int`, and in the `elif` it is a `String`. The compiler follows an early exit too: after a branch that returns, the rest of the function knows the test failed:

```moxie
union type Identifier = Int | String
fn weight(id Identifier) Int
  if id is String then return len(id)
  id + 1
println(weight("Node-04"))
println(weight(41))
```
**Output:**

```
7
42
```

The last line can add, because the only way to reach it is with an `Int`. And without the test:

```moxie
union type Identifier = Int | String
fn bad(id Identifier) Int
  id + 1
```
**The compiler says:**

```
error: `+` can't take `Int | String`: a value of a union is one of its members, so test it first (`if x is T` or a `when`)
```

## Mixing types in a collection

The elements of a `List`, `Set`, or `Array` share one type, so `List(1, "a")` is a compile error: it is usually a typo, and moxie won't guess a type that fits both. To mix on purpose, name a union where you declare the collection. The elements convert into it, and `when` takes them apart again:

```moxie
xs List[Int | String] = List(1, "a", 2)
for x in xs
  when x
    Int -> println("number $x")
    String -> println("text $x")
settings Dict[String, Int | Bool] = Dict("retries" -> 3, "verbose" -> true)
println(len(settings))
```
**Output:**

```
number 1
text a
number 2
2
```

An unannotated `mixed = List(1, "a")` is the error.

## Data paths: reaching into nested tuples

When tuples contain tuples, getting at a deep field and making a copy with it changed is tedious. A *data path* names a spot inside nested tuples. It begins with a type name and continues with fields, separated by `/`:

```moxie
tuple Firm(name String, floor Int)
tuple User(id Int, firm Firm)
a = User(1, Firm("Initech", 2))
firm_name = /User/firm/name
println(firm_name(a))
println((/User/firm/floor)(a))
```
**Output:**

```
Initech
2
```

A path is a function from a `User` to the value it names, so it can be stored, passed, and combined. Two functions, `replace` and `modify`, use a path to build a changed copy, rewriting the nested tuples around it. The original is untouched:

```moxie
tuple Firm(name String, floor Int) deriving show
tuple User(id Int, firm Firm) deriving show
a = User(1, Firm("Initech", 2))
b = replace(a, /User/firm/name, "Acme")
c = modify(a, /User/firm/name, (s) -> "$s Ltd")
println(a)
println(b)
println(c)
```
**Output:**

```
User(id: 1, firm: Firm(name: "Initech", floor: 2))
User(id: 1, firm: Firm(name: "Acme", floor: 2))
User(id: 1, firm: Firm(name: "Initech Ltd", floor: 2))
```

`replace` and `modify` need the path written out in the call. Paths compose with `~>`, the same operator that composes functions: `/User/firm ~> /Firm/name` goes first to the firm and then to its name.

## When to use which

| You want | Use |
|---|---|
| a clearer name for the same thing | `type` alias |
| two things that must never be confused | `opaque type` |
| "all of these fields together" | `tuple` |
| "exactly one of these named cases" | `enum` |
| "a value that could be an `Int` or a `String`" | `union type` |

---

[← Dicts and sets](17-dicts-and-sets.html) · [Contents](./) · [Patterns →](19-patterns.html)
