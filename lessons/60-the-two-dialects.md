# Moxie and moxie/gc side by side

@nogc
You are reading the GC-free guide. moxie has a second dialect, moxie/gc, that keeps the same language and swaps the memory model: one shared heap with a generational collector instead of sizes worked out ahead of time. This lesson lists what changes, with a short example of each, so you can read code written for either dialect. Every example below also runs in moxie/gc, and the guide for that dialect shows the other column.
@end

@gc
You are reading the moxie/gc guide. moxie has a second dialect, GC-free moxie, that keeps the same language but has no collector: every size is worked out ahead of time. This lesson lists what moxie/gc takes away from that dialect's limits, with a short example of each. The GC-free guide shows the other column.
@end

Patterns, pipes, generics, interfaces, results, fibers, and channels are the same in both dialects. Only the memory model changes, and with it a good deal of what the language has to forbid. A program written for GC-free moxie that leans on `String[n]`, `readonly` strings, `copy`, fixed capacities, or pools needs edits to run in moxie/gc.

## Collections grow

@nogc
A `List`, `Dict`, or `Set` has a capacity, written in brackets when you create it. Adding a new key to a full `Dict` aborts the program, and `put` is the form that hands back `Err(NO_SLOT)` for you to handle instead:

```moxie
d = Dict[String, Int][1]("a" -> 1)
when put(d, "b", 2)
  Ok(_) -> println("stored")
  Err(e) -> println("full")
```
```output
full
```
@end

@gc
A `List`, `Dict`, or `Set` grows as needed. A size in brackets is only a hint for how much room to start with:

```moxie
xs = List(1, 2)
xs += 3
xs += 4
println(xs)
println(xs.len())
```
```output
List(1, 2, 3, 4)
4
```
@end

`Array` and `MultiArray` carry their sizes in their types in both dialects, since they are flat blocks.

## Updates share structure

@gc
In moxie/gc, `List`, `Dict`, and `Set` are persistent: an update builds a new version that shares most of its storage with the old one. Holding on to old versions costs very little:

```moxie
a = List(1, 2, 3)
b = a + 4
println(a)
println(b)
```
```output
List(1, 2, 3)
List(1, 2, 3, 4)
```
@end

@nogc
In GC-free moxie an update of a `List` builds the new version in the space the program set aside, so the old and new versions are separate values, and the compiler counts both:

```moxie
a = List[Int][4](1, 2, 3)
b = a + 4
println(a)
println(b)
```
```output
List(1, 2, 3)
List(1, 2, 3, 4)
```
@end

## One kind of string

@nogc
Text in GC-free moxie comes in more than one form. A `String[n]` holds at most `n` bytes and lives wherever the value that holds it lives, and a `readonly` string lasts for the whole program:

```moxie
name String[8] = "Ada"
println(name)
println(len(name))
```
```output
Ada
3
```
@end

@gc
moxie/gc has a single `String` type. There is no `String[n]`, no `readonly`, and no "lasts until the next reset":

```moxie
name = "Ada"
println(name)
println(len(name))
```
```output
Ada
3
```
@end

## Closures can go anywhere

@gc
A function type in moxie/gc is just its signature, so a closure can be stored in a `Dict`, a tuple field, or a channel, and a function can return a different closure from each branch:

```moxie
fn pick(flag Bool, k Int) (Int) -> Int
  when flag
    true -> (n) -> n + k
    false -> (n) -> n * k
fns = List(pick(true, 3), pick(false, 3))
println("${fns(0)(10)} ${fns(1)(10)}")
```
```output
13 30
```
@end

@nogc
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
```output
13
30
```
@end

## Streams

@gc
A stream can be returned from a function, unless it borrows a resource such as an open file.
@end

@nogc
A stream works in place over what it reads from, so it can be passed down but not returned, and the pipeline is finished inside the function that built it.
@end

## Resources and fibers

@gc
Atoms, channels, timers, and futures can be created anywhere, loops included. Ownership and moves work as before. Fibers are created on demand, with no slots reserved in advance, and a cap is optional.
@end

@nogc
Atoms, channels, timers, and futures are counted resources: the compiler adds them up before the program starts (lesson 36), so they can't be created in a loop whose count it can't bound. Fibers have slots, one pool per fiber function.
@end

## Pauses and failure

@gc
The collector works in short slices, so pauses are short, not zero. A full heap ends the program, and a structure that keeps growing can use up memory even though the collector is running.
@end

@nogc
With no collector there are no collector pauses at all. What replaces them is a startup tally: a program that does not fit its memory budget doesn't start.
@end

## Choosing

Reach for GC-free moxie when you need a program whose worst case is known before it runs: firmware, a service with a fixed budget, anything where a pause is a bug. Reach for moxie/gc when you want the language without the bookkeeping. Both read the same, and a program that avoids the features above runs in both.
