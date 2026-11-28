# Eager and lazy evaluation

When a program calls a function, it has to decide when to compute each argument. *Eager* evaluation computes it before the call. *Lazy* evaluation waits until the value is needed, and may never compute it at all. Moxie is eager by default, and it gives you lazy forms where they pay off: in `and` and `or`, in the branches of an `if`, in a `lazy` parameter or binding, and in streams.

## Arguments are eager

An argument is computed before the call, even if the function never uses it:

```moxie
impure fn noisy(n Int) Int
  println("evaluating $n")
  n * 10

fn ignore(x Int) Int
  0

println(ignore(noisy(1)))
```
```output
evaluating 1
0
```

The argument ran, and the function ignored the result. That is what eager evaluation means.

## `and`, `or` and `if` are lazy in the part they skip

The right side of `and` and `or` runs only when the left side doesn't settle the answer, and an `if` runs only the branch it takes. So a branch that would divide by zero is safe when it is skipped:

```moxie
d Int = 0
println(d == 0 or 100 / d > 1)
println(d ~= 0 and 100 / d > 1)
println(if d == 0 then -1 else 100 / d)
```
```output
true
false
-1
```

The guard in front does the work, and the risky part never runs. This is the everyday form of laziness, and it is the reason a guard clause reads so well.

## A `lazy` binding runs on its first read

A `lazy` binding is computed the first time its name is read, and at most once. If the name is never read, its value is never computed, so a value that would fail is harmless:

```moxie
fn never_read(d Int) Int
  lazy v = 100 / d
  7

println(never_read(0))
```
```output
7
```

A `lazy` binding must have a pure initializer, because it runs at a moment the reader can't see. That is the rule from the previous lesson, applied to laziness.

## Streams are lazy recipes

A pipeline doesn't do any work until a terminal asks for a result, and it can describe an endless source, because only the items the terminal reads are ever produced:

```moxie
xs = List(1, 2, 3, 4, 5, 6, 7, 8)
println(xs |> filter((n) -> n % 2 == 0) |> take(2) |> collect())
```
```output
List(2, 4)
```

The filter ran only until `take` had its two items. Lesson 21 explains the pipeline shape, and lesson 39 covers infinite sequences.

## Why bother

- Eager evaluation is predictable: every argument is computed exactly once, in order, before the call.
- Laziness saves work and avoids errors that would never be seen, and it lets a source be infinite.
- Moxie keeps the two visible. A plain argument is eager, and a `lazy` parameter, binding or stream is marked as such.

## What to remember

- Arguments are computed before the call, whether or not the function uses them.
- `and`, `or`, and `if` skip the part they don't need.
- A `lazy` binding is computed on its first read, and only then.
- A stream computes only what its terminal consumes.
