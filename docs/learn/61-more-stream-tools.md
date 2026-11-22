---
layout: default
learn: true
title: "More stream tools: sources you build · Learning Guide moxie"
---
<p><small>Streams and pipelines</small></p>

# 26. More stream tools: sources you build

Lesson 25 covered the common stages. This lesson covers the rest of the toolbox: stages that tidy and combine streams, generators that make a stream from a seed, and how to make your own types into stream sources.

## Tidying and combining

`distinct()` drops repeats and keeps the first of each. `intersperse(x)` puts a separator between elements, `min_by(f)` and `max_by(f)` pick by a measure and return a `Result`, and `span(pred)` splits at the first element that fails the test:

```moxie
words = List("pear", "fig", "banana", "fig", "kiwi")
println(words |> distinct() |> collect())
joined = words
  |> distinct()
  |> intersperse("|")
  |> reduce("", _1 + _2)
println(joined)
println(words |> min_by(len))
println(words |> max_by(len))
(short, rest) = words |> span((w) -> len(w) < 6)
println("${short} ${len(rest)}")
```
**Output:**

```
List("pear", "fig", "banana", "kiwi")
pear|fig|banana|kiwi
Ok("fig")
Ok("banana")
List("pear", "fig") 3
```

`zip_with`, `flatten`, `cycle`, and `split_at` work the same way:

```moxie
sums = zip_with(_1 + _2, List(1, 2, 3), List(10, 20, 30)) |> collect()
flat = List(List(1, 2), List(3)) |> flatten() |> collect()
loop3 = List(1, 2) |> cycle() |> take(5) |> collect()
(head, tail) = List(1, 2, 3, 4) |> split_at(1)
println("${sums} ${flat} ${loop3} ${head} ${tail}")
```
**Output:**

```
List(11, 22, 33) List(1, 2, 3) List(1, 2, 1, 2, 1) List(1) List(2, 3, 4)
```

## Counting and grouping

`frequencies()` counts how often each element appears, `count_by(key)` counts by a computed key, and `distinct_by(key)` keeps the first element for each key:

```moxie
words = List("pear", "fig", "plum", "kiwi", "apple")
println(words |> count_by(len))
println(words |> distinct_by(len) |> collect())
println(List(1, 2, 1, 3, 1) |> frequencies())
```
**Output:**

```
Dict(4 -> 3, 3 -> 1, 5 -> 1)
List("pear", "fig", "apple")
Dict(1 -> 3, 2 -> 1, 3 -> 1)
```

## Generators with `unfold`

A generator is a function that returns an `unfold` stream. You give it a seed, and a step that takes the current state and returns `Ok((value, next_state))`, or `Err` to end the stream:

```moxie
tuple Fib deriving show
  a Int,
  b Int

fn fibonacci() Stream[Int]
  unfold(Fib(a: 0, b: 1))(s) ->
    Ok((s.a, Fib(a: s.b, b: s.a + s.b)))

for n in fibonacci() |> take(6)
  println(n)
```
**Output:**

```
0
1
1
2
3
5
```

The stream is lazy, so the infinite sequence costs nothing until something pulls from it, and `take(6)` pulls exactly six.

## Your own types as sources

A tuple or enum becomes a stream source when it has a method `to_stream(self)` that returns a `Stream[T]`. Its elements are `T` in every stage, and `for` walks it:

```moxie
tuple Countdown
  from Int

impl Countdown
  fn to_stream(self) Stream[Int] = (1..self.from) |> reverse()

c = Countdown(3)
println(c |> map(_ * 2) |> collect())
for n in c
  println("${n}...")
println("liftoff ${c |> sum()}")
```
**Output:**

```
List(6, 4, 2)
3...
2...
1...
liftoff 6
```

The method runs when the first element is pulled, so making a `Countdown` costs nothing, and the checker reads `Int` from the declared `Stream[Int]`, so `c |> map((s) -> s + "x")` is a compile error.

An `Option` is a source too, of zero or one element: `for x in maybe` runs once for a `Some` and not at all for a `None`.

## Streams over data you already have

A stream may not outlive the data it reads, so a function in GC-free moxie can't return a stream over one of its own local arrays. A function that wraps data the caller owns is declared `inline fn`, which makes the stream view the caller's data directly:

```moxie
tuple Packet deriving show
  id Int

tuple NetworkBuffer
  packets List[Packet]

inline fn stream_packets(buffer NetworkBuffer) Stream[Packet]
  Stream(buffer.packets, 0..)

buf = NetworkBuffer(packets: List(Packet(id: 1), Packet(id: 2)))
for p in stream_packets(buf)
  println(p)
```
**Output:**

```
Packet(id: 1)
Packet(id: 2)
```

*In the Spec: [13. Pipelines and streams](../spec.html#s13)*

---

[← Streams and pipelines](21-streams-and-pipelines.html) · [Contents](./) · [Pipe slots, `seq`, and doing work once →](50-pipe-slots-and-caching.html)
