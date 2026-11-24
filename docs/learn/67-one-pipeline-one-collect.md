---
layout: default
learn: true
title: "One pipeline, one collect · Moxie Mixer’s Guide"
---
# 26. One pipeline, one collect

In the Spec: [13. Pipelines and streams](../spec.html#s13)
{: .specref}

In moxie a collection doesn't have to be turned into a stream before you can run stages over it. A `List`, `Array`, `Set`, `Dict`, `String` (through `chars()`), range, or `Option` is a pipeline source as it stands, so a pipeline is the collection, then the stages, then one terminal. There is no `to_stream()` at the front, no conversion at the back, and `collect()` appears once, at the very end.

## Start from the collection

```moxie
names = List("mina", "lee", "ana", "zoe", "bo")
result = names
  |> filter((n) -> len(n) > 2)
  |> map(upper(_))
  |> sort()
  |> collect()
println(result)
```
**Output:**

```
List("ANA", "LEE", "MINA", "ZOE")
```

`names` goes straight into `filter`. The pipeline keeps the names longer than two letters, upper-cases them, sorts them, and builds the list once, at the end.

Every other kind of collection starts a pipeline the same way:

```moxie
tags = Set("x", "y")
println(tags |> map(upper(_)) |> sort() |> collect())
scores = Dict("ann" -> 90, "bob" -> 40, "cy" -> 75)
println(scores |> filter((k, v) -> v > 50) |> map((k, v) -> k) |> sort() |> collect())
println("hello" |> chars() |> filter(_ == 'l') |> count())
println(1..10 |> filter(_ % 2 == 0) |> collect())
println(Some(4) |> map(_ + 1) |> collect())
```
**Output:**

```
List("X", "Y")
List("ann", "cy")
2
List(2, 4, 6, 8, 10)
List(5)
```

A `Dict` hands each stage a key and a value as a pair, which is why `filter` and `map` above take two parameters. A `Set`, a `Dict` and a range all end up in a `List` at the end of the pipeline, because `collect()` always builds a `List`.

## Collect once, at the end

A `List` is itself a pipeline source, so it is possible to collect in the middle of a pipeline and carry on. It gives the same answer:

```moxie
names = List("mina", "lee", "ana", "zoe", "bo")
slow = names |> map((n) -> len(n)) |> collect() |> filter(_ > 2) |> collect()
fast = names |> map((n) -> len(n)) |> filter(_ > 2) |> collect()
println(slow)
println(fast)
println(slow == fast)
```
**Output:**

```
List(4, 3, 3, 3)
List(4, 3, 3, 3)
true
```

The first version builds a whole list of lengths in the middle, and the second pipeline walks it again. The second version never builds that list: each name travels through `map` and `filter` and into the result, one at a time. So write the stages one after another and put a single `collect()` (or `sum()`, `count()`, `reduce(...)`, or a `for` loop) at the end.

## Where you do convert

A function that declares a `Stream[T]` parameter wants a stream, and a plain collection is not one, so the call site converts it with `to_stream()`. A pipeline is already a stream, so it needs no conversion:

```moxie
fn evens(xs Stream[Int]) List[Int]
  xs |> filter(_ % 2 == 0) |> collect()
println(evens(List(1, 2, 3, 4) |> map(_ + 1)))
println(evens(List(1, 2, 3, 4) |> to_stream()))
println(evens(Set(2, 3) |> to_stream()))
```
**Output:**

```
List(2, 4)
List(2, 4)
List(2)
```

Functions such as `traverse` and `sequence` take streams in this way. A type of your own becomes a pipeline source when it has a `to_stream` method, which the lesson on more stream tools shows.

---

[← Streams and pipelines](21-streams-and-pipelines.html) · [Contents](./) · [More stream tools: sources you build →](61-more-stream-tools.html)
