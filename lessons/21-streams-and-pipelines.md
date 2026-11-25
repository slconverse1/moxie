# Pipelines and streams

A *stream* is a sequence of values produced one at a time. Instead of writing a loop that builds up a result, you describe a *pipeline*: where the values come from, what happens to each, and what you want at the end. Streams are the main tool for working with collections in moxie.

## The shape of a pipeline

A pipeline has a **source**, some **stages**, and a **terminal**, joined with `|>`:

```moxie
numbers = List(1, 2, 3, 4, 5, 6)
result = numbers
  |> filter(_ % 2 == 0)
  |> map(_ * 10)
  |> sum()
println(result)
```
```output
120
```

`numbers` is the source. `filter(...)` keeps the even ones, `map(...)` multiplies each by ten, and `sum()` is the terminal that produces the final number. The pipeline reads top to bottom, in the order things happen. A pipeline continues on the next line when that line begins with `|>`.

`_` stands for the element in a short function, so `_ % 2 == 0` is the function "is this one even". You can also write a full lambda: `filter((n) -> n % 2 == 0)`.

The same pipeline can be written with dots, which reads left to right and means exactly the same thing:

```moxie
numbers = List(1, 2, 3, 4, 5, 6)
println(numbers.filter(_ % 2 == 0).map(_ * 10).sum())
```
```output
120
```

## Sources

Any collection is a source: a `List`, `Array`, `Set`, `Dict` (as `(key, value)` pairs), a `String` through `chars()`, or a range. A range with no end is an *infinite* source, which is fine because a stream only produces values as the terminal asks for them:

```moxie
println(List(10, 20, 30) |> map(_ + 1) |> collect())
println("hello".chars() |> map(upper(_)) |> collect())
println(1.. |> filter(_ % 7 == 0) |> take(3) |> collect())
```
```output
List(11, 21, 31)
List("H", "E", "L", "L", "O")
List(7, 14, 21)
```

## Stages

A stage takes a stream and gives a stream. The common ones:

| Stage | What it does |
|---|---|
| `map(f)` | applies `f` to each element |
| `filter(pred)` | keeps elements for which `pred` is true |
| `take(n)`, `drop(n)` | the first `n`, or all but the first `n` |
| `take_while(pred)`, `drop_while(pred)` | the same, by a condition |
| `enumerate()` | pairs each element with its index, from 0 |
| `zip(other)` | pairs elements with another collection's |
| `concat(other)` | one stream after another |
| `flat_map(f)` | maps each element to a stream and joins them |
| `distinct()` | drops repeats |
| `scan(start, f)` | a running total, emitting each step |
| `sort()`, `reverse()` | in order, or backwards |
| `chunks(n)`, `windows(n)` | groups of `n`, or every run of `n` neighbors |

```moxie
xs = List(5, 3, 8, 1, 9, 2)
println(xs |> sort() |> collect())
println(xs |> reverse() |> collect())
println(xs |> take(2) |> collect())
println(xs |> drop(4) |> collect())
println(xs |> take_while(_ > 2) |> collect())
println(xs |> scan(0, _1 + _2) |> collect())
println(xs |> enumerate() |> collect())
println(xs |> zip(List("a", "b", "c")) |> collect())
println(xs |> chunks(4) |> collect())
println(xs |> windows(5) |> collect())
println(List(1, 1, 2, 2, 3) |> distinct() |> collect())
println(List(1, 2) |> flat_map((n) -> List(n, n * 10)) |> collect())
```
```output
List(1, 2, 3, 5, 8, 9)
List(2, 9, 1, 8, 3, 5)
List(5, 3)
List(9, 2)
List(5, 3, 8)
List(5, 8, 16, 17, 26, 28)
List((0, 5), (1, 3), (2, 8), (3, 1), (4, 9), (5, 2))
List((5, "a"), (3, "b"), (8, "c"))
List(List(5, 3, 8, 1), List(9, 2))
List(List(5, 3, 8, 1, 9), List(3, 8, 1, 9, 2))
List(1, 2, 3)
List(1, 10, 2, 20)
```

A stage that needs to see every element before it can produce the first, like `sort`, is *vertical*. A plain stage like `map` passes one element at a time through the whole chain, and nothing is computed for an element that a later `take` throws away.

## Terminals

A terminal ends the pipeline and gives a value:

```moxie
xs = List(5, 3, 8, 1, 9, 2)
println(xs |> sum())
println(xs |> count())
println(xs |> product())
println(xs |> max())
println(xs |> min())
println(xs |> first())
println(xs |> last())
println(xs |> any(_ > 8))
println(xs |> all(_ > 0))
println(xs |> find(_ > 5))
println(xs |> position(_ > 5))
println(xs |> reduce(0, _1 + _2))
println(xs |> avg())
println(xs |> collect())
```
```output
28
6
2160
Ok(9)
Ok(1)
Ok(5)
Ok(2)
true
true
Ok(8)
Ok(2)
28
Ok(4.666666666666667)
List(5, 3, 8, 1, 9, 2)
```

`max`, `min`, `first`, `last`, `find`, and `avg` give a `Result`, because an empty stream has no such element. The error is the standard `MISSING`. `sum` of an empty stream is zero, and `product` of one is one. `reduce(start, f)` combines all the elements into one value, starting from `start`, which is how you write your own aggregates.

`collect()` gathers the stream back into a `List`. `partition(pred)` splits into two lists, `unzip()` splits pairs, and `group_by(key)` and `frequencies()` build a `Dict`:

```moxie
xs = List(5, 3, 8, 1, 9, 2)
evens, odds = xs |> partition(_ % 2 == 0)
println("$evens $odds")
println(xs |> group_by(_ % 3))
println(List("a", "b", "a") |> frequencies())
println(List((1, "x"), (2, "y")) |> unzip())
```
```output
List(8, 2) List(5, 3, 1, 9)
Dict(2 -> List(5, 8, 2), 0 -> List(3, 9), 1 -> List(1))
Dict("a" -> 2, "b" -> 1)
(List(1, 2), List("x", "y"))
```

## for loops take streams too

A `for` loop can iterate over a pipeline, which is useful when you want the loop body to do something with each result:

```moxie
for (i, name) in List("ann", "bo") |> enumerate()
  println("$i: $name")
for v in List(10, 20, 30) |> map(_ + 1)
  println(v)
```
```output
0: ann
1: bo
11
21
31
```

## Where does the value go in a stage?

`|>` hands the value on its left to the stage on its right. By default it becomes the stream argument (the last argument), which is why `map(f)` works with only the function written. When you need the value to go somewhere else in an ordinary function call, mark the spot with `&`:

```moxie
fn subtract(x Int, y Int) Int = x - y
println(10 |> subtract(&, 3))
println(10 |> subtract(3, &))
```
```output
7
-7
```

If both placements would type-check, such as `10 |> subtract(3)`, the compiler reports an ambiguity and asks you to mark the spot with `&`, rather than guessing.

A stage with no arguments written takes the tuple from the stage before it, if it fits the whole parameter list:

```moxie
fn coordinates(id Int) (Int, Int) = (id * 2, id * 3)
fn describe(x Int, y Int) String = "at $x,$y"
println(7 |> coordinates() |> describe())
```
```output
at 14,21
```

## Streams are lazy, and run once

A stage doesn't run until a terminal asks for values. This pipeline shows the order, element by element, through the whole chain:

```moxie
fn tag_map(x Int) Int
  println("map $x")
  x * 2
fn tag_keep(y Int) Bool
  println("keep $y")
  y > 2
n = List(3, 1, 2) |> map(tag_map) |> filter(tag_keep) |> count()
println(n)
```
```output
map 3
keep 6
map 1
keep 2
map 2
keep 4
2
```

Each terminal re-runs the recipe from the source. If you need the values twice, `collect()` them into a list and use the list.

## Why streams, and not loops?

A loop says *how*: keep a counter, update a total, remember to stop. A pipeline says *what*: keep the evens, multiply, sum. The pipeline can't forget to reset an accumulator, and each stage is small enough to name and test. A `for` loop is still the right tool when the body has effects or when the iteration is genuinely stateful.
