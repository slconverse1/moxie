---
layout: default
learn: true
title: "Arrays and grids · Mixer’s Guide moxie"
---
<p class='eyebrow'>Data</p>

# 18. Arrays and grids

<div class='specref' markdown='1'>In the Spec: [7. Collections](../spec.html#s7)</div>

A `List` can be any length and can change length when you add to it. An `Array` has a size that is part of its type, fixed when the array is made. That makes arrays the right tool when the size is part of the meaning: three colour channels, eight bytes, a 3 by 3 board. It also lets the compiler catch mistakes about size before the program runs.

## Making an array

An array is written as a tuple of values in parentheses, with the type `Array[T]` written on the binding, and the size is taken from the value:

```moxie
numbers Array[Int] = (10, 20, 30, 40, 50)
println(numbers)
println(len(numbers))
println(numbers(0))
println(numbers(4))
```
**Output:**

```
Array(10, 20, 30, 40, 50)
5
10
50
```

`Array(10, 20, 30)` also builds one. Elements are read by position, from 0, just like a list.

## Sizes are checked

Because the size is in the type, an index that is certainly wrong is a compile error rather than a surprise:

```moxie
numbers Array[Int] = (10, 20, 30)
println(numbers(7))
```
**The compiler says:**

```
error: index 7 is past the end of `numbers`, which has 3 elements (the last index is 2)
```

When the index is only known at run time and turns out wrong, the program aborts with a diagnostic, so use `get` for the position you aren't sure about: it returns a `Result`, as it does for lists.

```moxie
numbers Array[Int] = (10, 20, 30)
println(get(numbers, 1))
println(get(numbers, 7))
```
**Output:**

```
Ok(20)
Err(Error(code: 4, message: "no such element"))
```

## Slices

A range in parentheses gives a *slice*, a view of part of the array. A slice is read-only, and its positions start at 0 again:

```moxie
numbers Array[Int] = (10, 20, 30, 40, 50)
middle = numbers(1..3)
println(middle)
println(middle(0))
println(len(middle))
```
**Output:**

```
Array(20, 30, 40)
20
3
```

With a constant range you can name the elements directly:

```moxie
numbers Array[Int] = (10, 20, 30, 40, 50)
(a, b, c) = numbers(1..3)
println("$a $b $c")
```
**Output:**

```
20 30 40
```

A slice in GC-free moxie is a *borrowed view* of the original, so it can't be returned from a function or stored, since it only makes sense while the array it came from is around. `copy(slice)` makes an array you own.

## Changing an element

Like everything else, arrays don't change in place. `set` gives back a new array with one position replaced, and an assignment to an element rebinds the name to the changed copy:

```moxie
numbers Array[Int] = (10, 20, 30)
changed = set(numbers, 1, 99)
println(changed)
println(numbers)
numbers(0) += 1
println(numbers)
```
**Output:**

```
Array(10, 99, 30)
Array(10, 20, 30)
Array(11, 20, 30)
```

## Looping

To visit every position, an exclusive range ends at `len`:

```moxie
numbers Array[Int] = (10, 20, 30)
for i in 0..<len(numbers)
  println("$i: ${numbers(i)}")
```
**Output:**

```
0: 10
1: 20
2: 30
```

When you only need the values, loop over the array itself:

```moxie
for n in Array(10, 20, 30)
  println(n)
```
**Output:**

```
10
20
30
```

## Patterns

An array pattern works like a list pattern:

```moxie
numbers Array[Int] = (10, 20, 30)
when numbers
  Array(first, ...rest) -> println("first $first, then ${len(rest)} more")
```
**Output:**

```
first 10, then 2 more
```

## Grids: arrays of more than one dimension

A `MultiArray` is a rectangular grid whose shape is in its type. A literal separates rows with `;`:

```moxie
grid MultiArray[Int][2, 3] = (
  10, 20, 30 ;
  40, 50, 60
)
println(grid(1, 2))
println(grid(0, 0))
```
**Output:**

```
60
10
```

`MultiArray[Int][2, 3]` is two rows of three columns. A literal with the wrong number of cells is a compile error, and an index outside the shape is too.

Slicing a grid: a bare number picks one row or column and drops that dimension, a range keeps the dimension, and `..` means the whole axis:

```moxie
grid MultiArray[Int][2, 3] = (
  10, 20, 30 ;
  40, 50, 60
)
row = grid(1, ..)
col = grid(.., 1)
block = grid(0..1, 1..2)
println(row)
println(col)
println(block)
```
**Output:**

```
Array(40, 50, 60)
Array(20, 50)
MultiArray(20, 30, 50, 60)
```

A grid of three dimensions separates the layers with `;;`, and slices the same way.

## Functions over any size

A function can take an array of any length, and read the length as a number, with a size parameter in brackets:

```moxie
fn total[N](a Array[Int][N]) Int
  a |> reduce(0, _1 + _2)
fn size_of[N](a Array[Int][N]) Int
  N
x Array[Int] = (1, 2, 3)
y Array[Int] = (1, 2, 3, 4, 5)
println(total(x))
println(total(y))
println(size_of(y))
```
**Output:**

```
6
15
5
```

A `where` clause limits the sizes a function accepts. This one can't be called with an empty array, and the compiler says so at the call:

```moxie
fn first_of[T, N where N > 0](a Array[T][N]) T
  a(0)
x Array[Int] = (1, 2, 3)
println(first_of(x))
```
**Output:**

```
1
```

Two arrays that must have the same length can share a size parameter. `dot` below accepts two arrays only if their sizes agree:

```moxie
fn dot[N](a Array[Int][N], b Array[Int][N]) Int
  zip(a, b) |> map()(x, y) -> x * y
  |> reduce(0, _1 + _2)
x Array[Int] = (1, 2, 3)
println(dot(x, x))
```
**Output:**

```
14
```

## Array or list?

Use a `List` when the number of elements isn't known up front or changes as the program runs. Use an `Array` when it is part of the meaning of the data, or you want the compiler to enforce it. Both are immutable values, and both work with the same stream operations, so changing from one to the other later is usually small.

---

[← Lists](15-lists.html) · [Contents](./) · [In-place algorithms: `mutable` blocks →](56-mutable-blocks.html)
