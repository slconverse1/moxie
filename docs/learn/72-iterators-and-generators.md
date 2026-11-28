---
layout: default
learn: true
title: "Iterators and generators · Moxie Mixer’s Guide"
---
# 71. Iterators and generators

An *iterator* is a source you can step through one item at a time. A *generator* is a recipe that makes a new iterator from a starting state, and it can go on forever, because items are produced only when they are asked for. Moxie uses the same `for` loop for both, so you learn one shape and use it everywhere.

## Any collection is a source

A `for` loop walks a collection in order. A list gives its items, a dictionary gives `(key, value)` pairs, and a range counts:

```moxie
ages = Dict("ann" -> 31, "bob" -> 25)
for (name, age) in ages
  println("$name is $age")

for n in 3..1 step -1
  println(n)

for n in (1..10 step 4)
  println(n)
```
**Output:**

```
ann is 31
bob is 25
3
2
1
1
5
9
```

A dictionary's pair can be taken apart in the loop header, as the pattern `(name, age)` shows. A range has a step, and the step can be negative, so `3..1 step -1` counts down.

## Stages between the source and the loop

A `for` loop can read from a pipeline, so filtering and mapping happen one item at a time, as the loop pulls them:

```moxie
for x in List(3, 1, 4) |> filter((n) -> n > 1)
  println(x)
```
**Output:**

```
3
4
```

No intermediate list is built. Each item goes through the filter, and the ones that pass go to the loop body. Lesson 21 explains pipelines in full.

## Building a new sequence with `for ... yield`

A `for` block with `yield` builds a new stream, which is lazy like any other. Each line before `yield` draws from a source, and `yield` says what each combination produces:

```moxie
sums = for
  a in List(1, 2)
  b in List(10, 20)
  yield a + b
println(sums |> collect())
```
**Output:**

```
List(11, 21, 12, 22)
```

## Generators: a recipe that makes an iterator

A generator takes a starting state and a step, and produces items for as long as the step says there is one. Because the stream is lazy, an infinite generator costs nothing until something pulls from it. The `unfold` function builds one, and lesson 61 shows a complete generator for the Fibonacci numbers:

```moxie
evens = unfold(0)(n) -> Ok((n, n + 2))
println(evens |> take(4) |> collect())
```
**Output:**

```
List(0, 2, 4, 6)
```

`take` asks for exactly four items, so the generator produces only those four.

## Iterators and generators together

Because both are streams, you can mix them freely. Here the generator gives the numbers, and the loop prints only the ones that match:

```moxie
evens = unfold(0)(n) -> Ok((n, n + 2))
for n in evens |> take_while(_ < 10)
  println(n)
```
**Output:**

```
0
2
4
6
8
```

## What to remember

- A `for` loop accepts any collection, a range, or a stream.
- A dictionary gives `(key, value)` pairs, and a range can step down with a negative step.
- Stages in a pipeline run one item at a time, with no intermediate list.
- `for ... yield` builds a new lazy stream.
- A generator (`unfold`) makes an iterator from a state, and it can be infinite, because only what is pulled is produced.

---

[← The pyramid of doom](71-the-pyramid-of-doom.html) · [Contents](./) · [Existential types →](73-existential-types.html)
