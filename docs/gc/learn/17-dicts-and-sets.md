---
layout: default
dialect: gc
learn: true
title: "Dicts and sets · Moxie/gc Mixer’s Guide"
---
# 20. Dicts and sets

<div class='specref' markdown='1'>In the Spec: [7. Collections](../spec.html#s7), [10. Operators](../spec.html#s10)</div>

A `Dict` maps keys to values: names to ages, ids to records, words to counts. A `Set` holds distinct values and answers "is this one of them?" quickly. Both keep their elements in the order they were added.

## Making a Dict

`Dict(...)` takes `key -> value` entries. A key is an ordinary expression, so a word is written as a string, `"alice" -> 30`, and a bare name such as `who -> 30` uses the *value* of the variable `who`:

```moxie
ages = Dict("alice" -> 30, "bob" -> 25, "carol" -> 41)
println(ages)
println(len(ages))
```
**Output:**

```
Dict("alice" -> 30, "bob" -> 25, "carol" -> 41)
3
```

All the keys have one type and all the values have one type, so this is a `Dict[String, Int]`. To mix types, name a union or an enum, which a later lesson shows.

In moxie/gc a dict grows as needed. A capacity, as in `Dict[String, Int][10]()`, is only an optional hint.

## Looking a key up

A lookup might find nothing, so `ages(alice)` is a `Result`: `Ok` with the value, or `Err` when the key is missing. You take it apart the way you take apart any `Result`:

```moxie
ages = Dict("alice" -> 30, "bob" -> 25)
when ages("alice")
  Ok(a) -> println("alice is $a")
  Err(e) -> println("no alice")
when ages("zed")
  Ok(a) -> println("zed is $a")
  Err(e) -> println("no zed")
```
**Output:**

```
alice is 30
no zed
```

In `ages("alice")` the key is a string. To look up with a variable, write its name, `ages(who)`, and `get_or` supplies a default:

```moxie
ages = Dict("alice" -> 30, "bob" -> 25)
who = "bob"
println(ages(who))
println(get_or(ages, "dave", 0))
println(get_or(ages, "bob", 0))
```
**Output:**

```
Ok(25)
0
25
```

## Walking a Dict

A `for` loop takes the entries as `(key, value)` pairs, in insertion order. `keys` and `values` give just one side:

```moxie
ages = Dict("alice" -> 30, "bob" -> 25, "carol" -> 41)
for (name, age) in ages
  println("$name is $age")
println(keys(ages) |> collect())
println(values(ages) |> collect())
```
**Output:**

```
alice is 30
bob is 25
carol is 41
List("alice", "bob", "carol")
List(30, 25, 41)
```

## Changing a Dict: making a new one

A Dict is a value, so an update gives a new Dict. A *spread* brings in the old entries, and the entries written after replace or add:

```moxie
ages = Dict("alice" -> 30, "bob" -> 25, "carol" -> 41)
older = Dict(...ages, "alice" -> 31, "dave" -> 7)
println(older)
println(len(ages))
println(len(older))
```
**Output:**

```
Dict("alice" -> 31, "bob" -> 25, "carol" -> 41, "dave" -> 7)
3
4
```

`ages` is unchanged. `alice -> 31` replaced the old `alice` where it stood, and `dave` is new, at the end. For a single change there is `put`, and `remove` makes a Dict without a key:

```moxie
ages = Dict[String, Int][4]("alice" -> 30, "bob" -> 25)
println(put(ages, "carol", 41))
println(remove(ages, "bob"))
```
**Output:**

```
Dict("alice" -> 30, "bob" -> 25, "carol" -> 41)
Dict("alice" -> 30)
```

In moxie/gc, `put` gives the updated dict directly, since a dict grows as needed and nothing can be full.

An assignment through a name does the same thing, rebinding it to a changed copy:

```moxie
ages = Dict[String, Int][10]()
ages("alice") = 30
ages("bob") = 25
ages("alice") = 31
println(ages)
```
**Output:**

```
Dict("alice" -> 31, "bob" -> 25)
```

## Keys of other types

Keys can be numbers, `Bool`, `Char`, strings, tuples, lists, enums, and unions of those. A computed key is written with a `$` for a variable or parentheses for an expression. Floats can't be keys, because equality on floats is unreliable; nor can Sets, Dicts, or functions.

```moxie
cells = Dict[(Int, Int), String][8]()
cells((0, 0)) = "start"
cells((1, 2)) = "goal"
println(cells)
when cells((1, 2))
  Ok(v) -> println("found $v")
  Err(e) -> println("missing")
```
**Output:**

```
Dict((0, 0) -> "start", (1, 2) -> "goal")
found goal
```

Enum keys use the case names directly:

```moxie
enum Color deriving eq, hash, show
  Red
  Green
  Blue
hours Dict[Color, Int] = Dict(Red -> 3, Green -> 5)
println(hours)
```
**Output:**

```
Dict(Color.Red -> 3, Color.Green -> 5)
```

## Sets

A `Set` holds each value once:

```moxie
base = Set(1, 2, 3)
println(base + 4)
println(base + 3)
println(remove(base, 2))
println(2 in base)
println(99 not in base)
println(len(base))
```
**Output:**

```
Set(1, 2, 3, 4)
Set(1, 2, 3)
Set(1, 3)
true
true
3
```

`+` adds an element, and adding one that is already there changes nothing.

Sets also have algebra. `+` between sets is union, `-` is difference, `&` is intersection, and `^` is the elements in exactly one of the two. `is_subset`, `is_superset` and `is_disjoint` ask questions:

```moxie
a = Set(1, 2, 3)
b = Set(2, 3, 4)
println(a + b)
println(a - b)
println(a & b)
println(a ^ b)
println(is_subset(Set(2, 3), a))
println(is_superset(a, Set(1)))
println(is_disjoint(a, Set(9)))
```
**Output:**

```
Set(1, 2, 3, 4)
Set(1)
Set(2, 3)
Set(1, 4)
true
true
true
```

## Counting and grouping

Streams can build a Dict from a collection. `frequencies()` counts how often each element occurs, and `group_by` collects the elements under a key:

```moxie
words = List("a", "b", "a", "c", "a", "b")
println(words |> frequencies())
println(words |> distinct() |> collect())
println(List(1, 2, 3, 4, 5, 6) |> group_by(_ % 3))
```
**Output:**

```
Dict("a" -> 3, "b" -> 2, "c" -> 1)
List("a", "b", "c")
Dict(1 -> List(1, 4), 2 -> List(2, 5), 0 -> List(3, 6))
```

---

[← In-place algorithms: `mutable` blocks](56-mutable-blocks.html) · [Contents](./) · [Naming types: aliases, opaque types, and unions →](18-types-of-types.html)
