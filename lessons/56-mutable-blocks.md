# In-place algorithms: `mutable` blocks

Moxie values never change, and a loop's rebindings don't leave the loop. For most code that is a gain. A few algorithms, though, are most naturally written as *loops that write into an array*: sorting, prefix sums, a sieve, union-find. A `mutable` block gives those algorithms the shape they want without giving up what moxie promises from outside.

## The problem it solves

Lesson 9 showed that a name bound inside a loop body is a new name that ends with the body, and that `x@1` reaches the name outside. For an algorithm with many updates to several names, writing `@1` everywhere gets noisy. A `mutable` block drops the bookkeeping altogether.

## A mutable block

Inside it, `x = e` declares `x` the first time and assigns to it after that (no rebinding, no shadowing), and `x += e`, `x(i) = e`, and `x.f = e` write into `x` from any depth of `for`, `while`, `if`, and `when`:

```moxie
fn running_totals(xs Array[Int][5]) Array[Int][5]
  mutable
    out = xs
    total = 0
    for i in 0..<5
      total += xs(i)
      out(i) = total
    out

println(running_totals(Array(3, 1, 4, 1, 5)))
```
```output
Array(3, 4, 8, 9, 14)
```

The block is an expression whose value is its last line.

## The rules inside

- A variable keeps the type it was declared with, so `total = "x"` after `total = 0` is an error.
- Outer names are read-only inside the block, unless they are copied in on an `in` line (`in total`), which makes a mutable local of the same name and leaves the outer one alone.
- The assignments are *guaranteed* in-place writes. That's the difference from an ordinary update, which is in place only when the old value is dead.
- To keep that safe, `b = a` inside the block *copies* `a`, values enter by copy and leave as plain immutable values, and a closure made inside takes the current values.

So the block is pure from the outside, and a `pure fn` may contain one. This is what Haskell's `ST` monad provides with `runST` and a rank-2 type, here as a block with a keyword.

### Bringing an outer value in

```moxie
fn doubled(xs Array[Int][3], start Int) Array[Int][3]
  mutable
    in start
    out = xs
    for i in 0..<3
      out(i) = xs(i) * 2 + start
      start += 1
    out

println(doubled(Array(1, 2, 3), 10))
```
```output
Array(12, 15, 18)
```

`start` is a mutable local inside the block; the caller's `start` is untouched.

## The `algo` package

A small standard package, `algo`, is written this way. Each function takes an array, copies it in, writes into the copy in place, and gives back an ordinary immutable array, so a caller sees pure functions:

| Function | What it does |
|---|---|
| `quicksort`, `heapsort`, `merge_sort` (stable), `counting_sort` | sorting |
| `binary_search` | the index of a key in a sorted array, as a `Result` |
| `prefix_sums` | running totals |
| `sieve` | a prime sieve over an array of flags |
| `components` | union-find over a list of edges |
| `rotate`, `shuffle` (seeded), `next_permutation` | rearranging |
| `knapsack` | the best value within a capacity |

```moxie
import algo

xs = Array(5, 2, 9, 1, 7)
sorted = algo.quicksort(xs)
println(sorted)
println(algo.binary_search(sorted, 7))
println(algo.binary_search(sorted, 4))
println(algo.prefix_sums(xs))
println(algo.rotate(xs, 2))
println(xs)
```
```output
Array(1, 2, 5, 7, 9)
Ok(3)
Err(Error(code: 4, message: "not found"))
Array(5, 7, 16, 17, 24)
Array(9, 1, 7, 5, 2)
Array(5, 2, 9, 1, 7)
```

The original `xs` is unchanged: `quicksort` worked on its own copy. And a sieve:

```moxie
import algo

flags Array[Bool][12] = Array(false, false, true, true, true, true, true, true, true, true, true, true)
primes = algo.sieve(flags)
for i in 0..<12
  if primes(i)
    print("${i} ")
println("")
```
```output
2 3 5 7 11 
```

## What to remember

- `mutable` makes `x = e` declare or assign, and `x(i) = e` write in place, from any depth of loops and branches.
- Values enter by copy and leave as plain immutable values, so the block is pure from outside.
- Use it for sorting, sieves, and other loops that write arrays; use streams and `reduce` for everything else.
- `import algo` has ready-made in-place algorithms behind pure signatures.
