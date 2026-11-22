---
layout: default
title: "Lists · Learn moxie"
---
<p><small>Data</small></p>

# 17. Lists

A `List` holds a sequence of values of one type. It is the collection you will use most.

## Making a list

`List(...)` builds one. The elements must all have the same type, and the compiler works out the list's type from them:

```moxie
primes = List(2, 3, 5, 7, 11)
names = List("Ann", "Bo", "Cy")
println(primes)
println(names)
println(len(primes))
println(is_empty(primes))
```
**Output:**

```
List(2, 3, 5, 7, 11)
List("Ann", "Bo", "Cy")
5
false
```

`primes` is a `List[Int]` and `names` is a `List[String]`. A list that mixes types is a compile error; the lesson on unions shows how to say "an `Int` or a `String`" on purpose.

## Reading elements

An element is read by its position in parentheses, counting from 0. A range in parentheses gives a slice:

```moxie
xs = List(10, 20, 30, 40, 50)
println(xs(0))
println(xs(4))
println(xs(1..3))
println(xs(3..))
println(xs(..<2))
```
**Output:**

```
10
50
List(20, 30, 40)
List(40, 50)
List(10, 20)
```

A position past the end *aborts* the program, because that is a bug, not a condition to handle. When the position might be wrong, `get` gives a `Result` instead, and `first` and `last` do too, since an empty list has neither:

```moxie
xs = List(10, 20, 30)
println(get(xs, 1))
println(get(xs, 7))
println(first(xs))
println(last(xs))
println(first(List[Int]()))
```
**Output:**

```
Ok(20)
Err(Error(code: 4, message: "no such element"))
Ok(10)
Ok(30)
Err(Error(code: 4, message: "empty"))
```

## Lists never change

Like every moxie value, a list is never changed in place. `+` makes a new list with an element or another list added, and `*` repeats. `remove` and `remove_at` make a new list without something:

```moxie
base = List(10, 20, 30)
longer = base + 40
combined = longer + List(50, 60)
println(base)
println(combined)
println(remove(combined, 30))
println(remove_at(combined, 1))
println(List(1, 2) * 2)
```
**Output:**

```
List(10, 20, 30)
List(10, 20, 30, 40, 50, 60)
List(10, 20, 40, 50, 60)
List(10, 30, 40, 50, 60)
List(1, 2, 1, 2)
```

`base` is still `List(10, 20, 30)` after all that. Because nothing is shared and mutable, you never wonder who else is holding the list.

To "change" an element, make a new list with the change, with `name(position) = value`. This rebinds the name to a modified copy:

```moxie
xs = List(10, 20, 30)
ys = xs
ys(0) = 99
println(ys)
println(xs)
```
**Output:**

```
List(99, 20, 30)
List(10, 20, 30)
```

There is no `push` or `append`. To add to a list in a loop, rebind it with `+`:

```moxie
squares = List[Int]()
for n in 1..5
  squares@1 += n * n
println(squares)
```
**Output:**

```
List(1, 4, 9, 16, 25)
```

`List[Int]()` is an empty list of integers. (Often a comprehension or `map` is a better way to build a list, below.)

In GC-free moxie a list has a *capacity*, the room reserved for its elements. A list made from a literal grows to fit what `+` and `*` produce. A list declared with a larger capacity keeps it, and aborts if it fills, which is how moxie keeps memory use predictable. Write the capacity in brackets after the type, as in `List[Int][100]()`.

## Looping and testing membership

```moxie
xs = List("a", "b", "c")
for x in xs
  println(x)
println("b" in xs)
println("z" in xs)
println("z" not in xs)
```
**Output:**

```
a
b
c
true
false
true
```

## Transforming a list

`map` applies a function to each element, `filter` keeps the elements that pass a test, and `sum`, `max`, `count` and `reduce` boil a list down to one value. These are *stream* operations, joined with the pipe `|>` and ended with `collect()` when you want a list back. The lesson on streams explains them fully; here is the shape:

```moxie
xs = List(1, 2, 3, 4, 5, 6)
println(xs |> map(_ * 10) |> collect())
println(xs |> filter(_ % 2 == 0) |> collect())
println(xs |> sum())
println(max(xs))
println(xs |> reduce(1, _1 * _2))
println(xs |> sort() |> reverse() |> collect())
```
**Output:**

```
List(10, 20, 30, 40, 50, 60)
List(2, 4, 6)
21
Ok(6)
720
List(6, 5, 4, 3, 2, 1)
```

`max` and `first` give a `Result` (an empty list has no maximum), which the output shows as `Ok(6)`. Using the dot form, `xs.map(...).filter(...).collect()` reads the same way and means the same thing.

## Building a list with a comprehension

A *comprehension* builds a list from a loop-shaped description:

```moxie
println(List(i * i for i in 1..6))
println(List(n for n in 1..20 if n % 3 == 0))
```
**Output:**

```
List(1, 4, 9, 16, 25, 36)
List(3, 6, 9, 12, 15, 18)
```

Nested loops use the block form, `for` with `yield`, which gives a stream, so `collect()` turns it into a list. Each line before `yield` draws from a source, and `yield` says what each combination produces (the lesson on streams returns to this):

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

## Lists of lists

Elements can be lists, which gives rows and columns. The element type is written `List[List[Int]]`:

```moxie
grid = List(List(1, 2, 3), List(4, 5, 6))
println(grid(1)(2))
for row in grid
  println(row |> sum())
```
**Output:**

```
6
6
15
```

When the grid is a real rectangle, the lesson on arrays shows a type that knows its shape.

## Taking a list apart with a pattern

A list pattern names the first element and the rest, and is the foundation of recursion over lists:

```moxie
fn describe(xs List[Int]) String
  when xs
    List() -> "empty"
    List(x) -> "just $x"
    List(first, ...rest) -> "$first and ${len(rest)} more"
println(describe(List()))
println(describe(List(7)))
println(describe(List(7, 8, 9)))
```
**Output:**

```
empty
just 7
7 and 2 more
```

---

[← Missing values and failures: Option and Result](14-missing-and-failed.html) · [Contents](./) · [Arrays and grids →](16-arrays.html)
