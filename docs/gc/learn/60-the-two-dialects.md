---
layout: default
dialect: gc
title: "Moxie and moxie/gc side by side · Learning Guide moxie/gc"
---
<p><small>Your program and its machine</small></p>

# 64. Moxie and moxie/gc side by side


You are reading the moxie/gc guide. moxie has a second dialect, GC-free moxie, that keeps the same language but has no collector: every size is worked out ahead of time. This lesson lists what moxie/gc takes away from that dialect's limits, with a short example of each. The GC-free guide shows the other column.

Patterns, pipes, generics, interfaces, results, fibers, and channels are the same in both dialects. Only the memory model changes, and with it a good deal of what the language has to forbid. A program written for GC-free moxie that leans on `String[n]`, `readonly` strings, `copy`, fixed capacities, or pools needs edits to run in moxie/gc.

## Collections grow


A `List`, `Dict`, or `Set` grows as needed. A size in brackets is only a hint for how much room to start with:

```moxie
xs = List(1, 2)
xs += 3
xs += 4
println(xs)
println(xs.len())
```
**Output:**

```
List(1, 2, 3, 4)
4
```

`Array` and `MultiArray` carry their sizes in their types in both dialects, since they are flat blocks.

## Updates share structure

In moxie/gc, `List`, `Dict`, and `Set` are persistent: an update builds a new version that shares most of its storage with the old one. Holding on to old versions costs very little:

```moxie
a = List(1, 2, 3)
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


moxie/gc has a single `String` type. There is no `String[n]`, no `readonly`, and no "lasts until the next reset":

```moxie
name = "Ada"
println(name)
println(len(name))
```
**Output:**

```
Ada
3
```

## Closures can go anywhere

A function type in moxie/gc is just its signature, so a closure can be stored in a `Dict`, a tuple field, or a channel, and a function can return a different closure from each branch:

```moxie
fn pick(flag Bool, k Int) (Int) -> Int
  when flag
    true -> (n) -> n + k
    false -> (n) -> n * k
fns = List(pick(true, 3), pick(false, 3))
println("${fns(0)(10)} ${fns(1)(10)}")
```
**Output:**

```
13 30
```


## Streams

A stream can be returned from a function, unless it borrows a resource such as an open file.


## Resources and fibers

Atoms, channels, timers, and futures can be created anywhere, loops included. Ownership and moves work as before. Fibers are created on demand, with no slots reserved in advance, and a cap is optional.


## Pauses and failure

The collector works in short slices, so pauses are short, not zero. A full heap ends the program, and a structure that keeps growing can use up memory even though the collector is running.


## Choosing

Reach for GC-free moxie when you need a program whose worst case is known before it runs: firmware, a service with a fixed budget, anything where a pause is a bug. Reach for moxie/gc when you want the language without the bookkeeping. Both read the same, and a program that avoids the features above runs in both.

---

[← Byte streams: Reader and Writer](65-byte-streams.html) · [Contents](./) · […moxie: the rest of the toolbox →](66-the-rest-of-moxie.html)
