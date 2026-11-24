---
layout: default
learn: true
title: "Moxie and moxie/gc side by side · Moxie Mixer’s Guide"
---
# 65. Moxie and moxie/gc side by side

In the Spec: [3. Memory model: S-space, T-space, and resets](../spec.html#s3), [24a. Departures from compile-time type safety](../spec.html#s24a)
{: .specref}

You are reading the GC-free guide. moxie has a second dialect, moxie/gc, that keeps the same language and swaps the memory model: one shared heap with a generational collector instead of sizes worked out ahead of time. This lesson lists what changes, with a short example of each, so you can read code written for either dialect. Every example below also runs in moxie/gc, and the guide for that dialect shows the other column.


Patterns, pipes, generics, interfaces, results, fibers, and channels are the same in both dialects. Only the memory model changes, and with it a good deal of what the language has to forbid. A program written for GC-free moxie that leans on `String[n]`, `readonly` strings, `copy`, fixed capacities, or pools needs edits to run in moxie/gc.

## Collections grow

A `List`, `Dict`, or `Set` has a capacity, written in brackets when you create it. Adding a new key to a full `Dict` aborts the program, and `put` is the form that hands back `Err(NO_SLOT)` for you to handle instead:

```moxie
d = Dict[String, Int][1]("a" -> 1)
when put(d, "b", 2)
  Ok(_) -> println("stored")
  Err(e) -> println("full")
```
**Output:**

```
full
```


`Array` and `MultiArray` carry their sizes in their types in both dialects, since they are flat blocks.

## Updates share structure


In GC-free moxie an update of a `List` builds the new version in the space the program set aside, so the old and new versions are separate values, and the compiler counts both:

```moxie
a = List[Int][4](1, 2, 3)
b = a + 4
println(a)
println(b)
```
**Output:**

```
List(1, 2, 3)
List(1, 2, 3, 4)
```

## One kind of string

Text in GC-free moxie comes in more than one form. A `String[n]` holds at most `n` bytes and lives wherever the value that holds it lives, and a `readonly` string lasts for the whole program:

```moxie
name String[8] = "Ada"
println(name)
println(len(name))
```
**Output:**

```
Ada
3
```


## Closures can go anywhere


A closure in GC-free moxie has a size that depends on what it captures, so the compiler keeps closures where it can measure them. A function can be passed down to another function and called there, but it can't be stored in a `Dict` or returned from different branches. The next best thing is data that names the behavior:

```moxie
enum Op deriving show
  Add
  Mul

fn apply(op Op, k Int, n Int) Int
  when op
    Add -> n + k
    Mul -> n * k

println(apply(Add, 3, 10))
println(apply(Mul, 3, 10))
```
**Output:**

```
13
30
```

## Streams


A stream works in place over what it reads from, so it can be passed down but not returned, and the pipeline is finished inside the function that built it.

## Resources and fibers


Atoms, channels, timers, and futures are counted resources: the compiler adds them up before the program starts (lesson 36), so they can't be created in a loop whose count it can't bound. Fibers have slots, one pool per fiber function.

## Pauses and failure


With no collector there are no collector pauses at all. What replaces them is a startup tally: a program that does not fit its memory budget doesn't start.

## Choosing

Reach for GC-free moxie when you need a program whose worst case is known before it runs: firmware, a service with a fixed budget, anything where a pause is a bug. Reach for moxie/gc when you want the language without the bookkeeping. Both read the same, and a program that avoids the features above runs in both.

---

[← Byte streams: Reader and Writer](65-byte-streams.html) · [Contents](./) · […moxie: the rest of the moxie toolbox →](66-the-rest-of-moxie.html)
