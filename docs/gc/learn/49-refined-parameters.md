---
layout: default
dialect: gc
title: "Refined parameters: proofs in the signature · Learning Guide moxie/gc"
---
<p><small>Fields and promises</small></p>

# 56. Refined parameters: proofs in the signature

A `requires` line says what a function needs, and a bad call fails when it runs. A **refined parameter** says it in the signature, and a bad call fails when you *compile*. Write `where` and a condition after the parameter's type:

```moxie
fn get(xs List[Int], i Int where i >= 0 and i < len(xs)) Int
  xs(i)
fn first_or(xs List[Int], fallback Int) Int
  if len(xs) > 0 then get(xs, 0) else fallback
fn last_or(xs List[Int], fallback Int) Int
  n = len(xs)
  if n > 0 then get(xs, n - 1) else fallback
println(first_or(List(4, 5, 6), 0))
println(last_or(List(4, 5, 6), 0))
println(last_or(List(), 7))
```
**Output:**

```
4
6
7
```

Each call to `get` has to be *proved*. In `first_or`, the test `len(xs) > 0` is enough to show that index `0` is in range. In `last_or`, `n` is bound to `len(xs)`, so `n - 1` is in range when `n > 0`. Remove either test and the call is a compile error that shows the condition it couldn't prove.

The checker uses what it can see: the function's own `where` clauses, the tests of an `if`/`elif`/`else`, an early `return ... if`, the range of `for i in 0..<len(xs)`, a name bound once to a sum or difference, constants, and the range of a bounded integer (`k Int[1..10]`). It reasons about whole numbers with `+`, `-`, a constant factor, and comparisons, and it is exact for those. Anything else, such as a product of two variables, is "unknown", and unknown is an error with the same message: check it first, or give the caller the same `where`.

Here is what a missing test looks like:

```moxie
fn half(n Int where n > 0) Int
  n / 2

fn careless(n Int) Int
  half(n)

println(careless(4))
```
**The compiler says:**

```
error: can't prove `n > 0` for the call to `half`: check it first (`if ... then half(...)`), or give this function the same `where`
```

And two ways to satisfy it, a test and a bounded type:

```moxie
fn half(n Int where n > 0) Int
  n / 2
fn safe_half(n Int) Int
  if n > 0 then half(n) else 0
fn pct_half(p Int[1..100]) Int
  half(p)
println(safe_half(9))
println(safe_half(-3))
println(pct_half(50))
```
**Output:**

```
4
0
25
```

The bounded type `Int[1..100]` already says `p > 0`, so `pct_half` needs no test. Rebinding a name forgets what was known about it, and so does `+=`, a `ref` argument, or a `ref` method on it.

The condition is also kept as a `requires`, so a call the compiler can't see, such as one through a function value, is still checked when it runs:

```moxie
fn pick(xs List[Int], i Int where i >= 0 and i < len(xs)) Int
  xs(i)
f (List[Int], Int) -> Int = pick
println(f(List(1, 2), 1))
```
**Output:**

```
2
```

A call `f(List(1, 2), 5)` here would abort with `requires failed in pick`, naming the caller as the bug.

Mistakes: calling a refined function with no test in front of it, testing only half of a condition (`i >= 0` for `i >= 0 and i < len(xs)`), changing the name between the test and the call (`i = 7`), putting a float or a string in a `where` the solver can't read (only integer comparisons are proved), and expecting a `where` on a `ref` parameter (it is checked at run time only).

## Refined aliases

A condition you use often can have a name. A **refined alias** adds `where` to a type alias, and `self` stands for the value:

```moxie
type Pos = Int where self > 0
type Pct = Int where self >= 0 and self <= 100
fn half(n Pos) Int
  n / 2
fn twice_half(m Pos) Int
  half(m) * 2
fn describe(p Pct) String
  "${p} percent"
println(twice_half(8))
println(half(7))
println(describe(40))
```
**Output:**

```
8
3
40 percent
```

A parameter declared `n Pos` means `n Int where n > 0`, nothing more, so every call has to prove `n > 0`, and `twice_half` can call `half(m)` because `m` is a `Pos`. The alias is the same type as `Int`, but the condition is enforced wherever you declare it.

- A binding `x Pos = v` is proved like a call: `x Pos = 0` is a compile error, and `x Pos = n` needs a test of `n` first (`if n > 0 then`). After it, `x` is known to be positive, so `half(x)` is accepted.
- A function declared to return `Pos` is checked as it returns (it means `ensures result > 0`), and a field declared `Pos` is checked whenever the tuple is built (it means `invariant balance > 0`); an abort in either names the function or tuple that broke the promise.
- A binding from a function that returns `Pos` needs no further proof.
- A `List[Pos]` (or `Array`, `Set`, `Dict` values) is checked element by element when the program runs; that check is not proved at compile time.
- An alias can be exported from a package (`export type Pos = Int where self > 0`) and used as `lib.Pos` after `import lib`, or as `Pos` after `import lib(Pos)`, provided its condition uses only `self` and literals.

Mistakes: `half(k)` for a plain `Int` `k` with no test first, and `x Pos = n` for an unchecked `n`.

```moxie
type Pos = Int where self > 0
tuple Account deriving show
  balance Pos
  name String
fn half(n Pos) Int
  n / 2
fn open_amount(n Int) Int
  if n > 0 then
    x Pos = n
    half(x) * 2
  else
    0
println(open_amount(9))
println(Account(balance: 40, name: "ann"))
```
**Output:**

```
8
Account(balance: 40, name: "ann")
```

`Account(balance: 0, name: "ann")` would abort with `invariant of Account failed: balance > 0`.

## What to remember

- `fn f(x Int where x > 0)` puts a condition in the signature; every call must prove it, or fail to compile.
- The checker proves what it can from tests, ranges, and bounded types; unknown is an error.
- The condition is kept as a `requires`, so calls through function values are still checked at run time.
- `type Pos = Int where self > 0` names a condition; parameters, bindings, results, and fields declared with it are all checked.

---

[← Properties, field delegates, and proxies](48-properties-delegates-proxies.html) · [Contents](./) · [Contracts: requires, ensures, invariant →](55-contracts.html)
