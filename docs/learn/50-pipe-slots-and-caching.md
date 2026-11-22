---
layout: default
learn: true
title: "Pipe slots, `seq`, and doing work once · Learner’s Guide moxie"
---
<p><small>Streams and pipelines</small></p>

# 27. Pipe slots, `seq`, and doing work once

Lesson 25 used `|>` to run values through stages. This lesson looks at how a pipe decides where the value goes, adds the `seq` block, and then turns to the opposite problem: doing an expensive step only once. Moxie never caches behind your back, so each way of reusing work is something you write on purpose.

## Where does the piped value go?

`|>` tries the first and the last mandatory parameter of the call on its right as the slot for the value on its left, fills the rest from the explicit arguments in order, and keeps the placement that type-checks. If a slot in the middle is needed, or the choice is unclear, write `&` where the value goes:

```moxie
fn add(x Int, y Int) Int
  x + y

fn multiply(factor Int, value Int) Int
  factor * value

final_score = 10
  |> add(5, &)
  |> multiply(2, &)
println(final_score)
```
**Output:**

```
30
```

If both the first and last parameter would accept the value, that is an ambiguity error that asks for `&`:

```moxie
fn subtract(a Int, b Int) Int
  a - b

x = 10 |> subtract(3)
println(x)
```
**The compiler says:**

```
error: `subtract` is ambiguous here: the piped value fits both the first and the last parameter. Write `&` where it goes, as in `subtract(&, ...)` or `subtract(..., &)`
```

Writing `&` settles it:

```moxie
fn subtract(a Int, b Int) Int
  a - b

println(10 |> subtract(&, 3))
println(10 |> subtract(3, &))
```
**Output:**

```
7
-7
```

A stage is always a call, and there's no partial application: `|> update_physics` without parentheses is an error.

### The dot form

The dot form is the same call, and you may use either:

```moxie
numbers = Array(1, 2, 3, 4)
a = numbers |> map(_ * 2) |> take(3) |> sum()
b = numbers.map(_ * 2).take(3).sum()
println("${a} ${b}")
```
**Output:**

```
12 12
```

### Tuples flow through stages

A stage with no explicit arguments takes a tuple that fits its whole parameter list, so results flow from one stage to the next:

```moxie
fn fetch_sensor_data(id Int) (Float, Float, Float)
  (12.5, 45.0, 0.8)

fn calculate_velocity(x Float, y Float, z Float) (speed Float, angle Float)
  (95.2, 14.6)

fn update_physics(speed Float, angle Float) Unit
  println("Physics vector updated: speed ${speed}, angle ${angle}")

1042
  |> fetch_sensor_data()
  |> calculate_velocity()
  |> update_physics()
```
**Output:**

```
Physics vector updated: speed 95.2, angle 14.6
```

Mistakes: piping a larger tuple into a smaller parameter list (extra fields are an error), and writing a stage without parentheses.

## `seq`: run every arm that applies

A `seq` block runs every arm whose condition holds, in order, each seeing the previous result:

```moxie
fn is_big(n Int) Bool
  n > 100

fn halve(n Int) Int
  n / 2

shrunk = 500
  |> seq
    is_big -> halve()
    is_big -> halve()
println(shrunk)
```
**Output:**

```
125
```

500 is big, so it halves to 250, which is still big, so it halves to 125, and the second arm's condition now fails if it were checked a third time. A `seq` needs piped input and has no default arm. It differs from `when`, which runs only the *first* arm that matches.

## Nothing is cached for you

Nothing is memoized, and nothing is cached behind your back. Caching is something you write on purpose, and moxie gives you these ways:

- `lazy` on a binding or a property computes one pure expression once, on its first read (lesson 58);
- a `lazy` parameter (call by need) evaluates its argument once, only if the body reads it;
- a bottom-up `reduce`, below, carries only what the next step needs;
- a `Dict` threaded through a recursion as a `ref` parameter lets calls share work;
- for a table many fibers share, one cache fiber (or an `Atom`) owns it and answers over channels.

### The bottom-up `reduce`

For a function of a changing argument, the usual recipe is to start from the base case and carry only what the next step needs. For Fibonacci that is the last two values:

```moxie
fn fib(n Int) Int
  (a, _) = 1..n |> reduce((0, 1), (s, _) -> (s(1), s(0) + s(1)))
  a

println(fib(10))
```
**Output:**

```
55
```

A grid of paths (move right or down, count the ways to the far corner) carries one row, and each new row is a `reduce` over the columns:

```moxie
fn next_row(prev List[Int]) List[Int]
  1..<len(prev) |> reduce(List(prev(0)), (acc, j) -> acc + (prev(j) + acc(j - 1)))

fn paths(rows Int, cols Int) Int
  first = List(1 for _ in 0..<cols)
  last = 1..<rows |> reduce(first, (prev, _) -> next_row(prev))
  last(cols - 1)

println("${paths(3, 3)} ${paths(10, 10)}")
```
**Output:**

```
6 48620
```

The same shape handles the longest common subsequence of two strings: carry the previous row of lengths, and build each new row from it and from the cell to its left:

```moxie
fn step(prev List[Int], acc List[Int], ys List[Char], x Char, j Int) Int
  if ys(j - 1) == x
    prev(j - 1) + 1
  else
    max(prev(j), acc(j - 1))

fn lcs_row(prev List[Int], x Char, ys List[Char]) List[Int]
  1..len(ys) |> reduce(List(0), (acc, j) -> acc + step(prev, acc, ys, x, j))

fn lcs(a String, b String) Int
  xs = List(c for c in chars(a))
  ys = List(c for c in chars(b))
  last = xs |> reduce(List(0 for _ in 0..len(ys)), (prev, x) -> lcs_row(prev, x, ys))
  last(len(ys))

println(lcs("ABCBDAB", "BDCABA"))
```
**Output:**

```
4
```

Memory is the size of what's carried, not of the whole table, and there is no cache to empty.

Reach for the next recipe when the subproblems aren't visited in a fixed order: thread a `Dict` through the recursion as a `ref` parameter, and wrap it in a plain function that starts it empty.

## What to remember

- `|>` tries the first and last parameter; write `&` where the value must go.
- A stage is a call; a tuple result can feed a stage with no explicit arguments.
- `seq` runs every arm that applies, in order, each seeing the previous result.
- No hidden caching: use `lazy`, a bottom-up `reduce`, a `ref` Dict, or a cache fiber.

*In the Spec: [13. Pipelines and streams](../spec.html#s13), [14. Caching, memoization, and effects](../spec.html#s14)*

---

[← More stream tools: sources you build](61-more-stream-tools.html) · [Contents](./) · [Fibers and channels →](22-fibers-and-channels.html)
