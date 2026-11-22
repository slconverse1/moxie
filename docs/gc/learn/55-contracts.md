---
layout: default
dialect: gc
learn: true
title: "Contracts: where and invariant · Mixer’s Guide moxie/gc"
---
<p class='eyebrow'>Fields and promises</p>

# 60. Contracts: where and invariant

<div class='specref' markdown='1'>In the Spec: [9c. Contracts](../spec.html#s9c)</div>

A contract states what a function needs and what it promises, in the code and not in a comment. It is for faults that are *bugs*: an expected failure, such as a missing file, still returns a `Result` (lesson 16). A contract failure ends the program with a message that says whose fault it was.

- A `where` after a parameter is a **precondition** that the caller must meet.
- A `where` after the result type is a **postcondition** that the function guarantees.
- An `invariant` is a condition that every value of a tuple type must satisfy.

## `where` on parameters and results

A condition goes in the signature, next to the thing it constrains. It may mention the parameters before it, and several conditions are joined with `and`. A condition after the result type may name `result`:

```moxie
fn inc(x Int where x > 0) Int where result > x
  x + 1

println(inc(1))
```
**Output:**

```
2
```

Arguments never change, so a postcondition can also refer to the arguments as they were. There is no `old`. For a `ref` parameter it sees the final value. (Older code may have written these as `requires` and `ensures` lines in the body; those are now a syntax error that says to write `where`.)

### Who is to blame

A call checks the preconditions, runs the body, checks the invariants of any value it built, and then checks the postconditions. A failed precondition is a **caller bug**, and a failed `invariant` or postcondition is a **supplier bug**. The message says which, and names the condition, the function, and the line:

```moxie
fn inc(x Int where x > 0) Int where result > x
  x + 1

z = 0
println(inc(z))
```
**The compiler says:**

```
abort in fiber main (line 5): precondition failed in inc: x > 0 (caller bug)
```

Here the function was given a value it said it couldn't take. When the *function* is wrong, it's a postcondition that fails. This body is arithmetic the checker can't follow, so the failure shows up when the program runs:

```moxie
fn bad(x Int) Int where result > x
  x * x - x * x

println(bad(5))
```
**The compiler says:**

```
abort in fiber main (line 4): postcondition failed in bad: result > x (supplier bug)
```

When the checker *can* follow the body, it catches the broken promise before the program runs:

```moxie
fn worse(x Int) Int where result > x
  x - 1

println(worse(5))
```
**The compiler says:**

```
error: `worse` promises `result > x`, but the value returned here can never satisfy it
```

A precondition whose arguments are all constants and that fails is a compile error, as a constant index out of range is:

```moxie
fn inc(x Int where x > 0) Int
  x + 1

println(inc(0))
```
**The compiler says:**

```
error: this call to `inc` always fails its precondition `x > 0` (x = 0)
```

## `invariant`

A tuple may end its fields with `invariant` lines. Values never change, so an invariant needs checking only where a value is built: a constructor call, a rebuild with `...p`, a field update (which rebuilds), and `read`. Every value of that type that exists therefore satisfies it:

```moxie
tuple Account deriving show
  owner String
  balance Int
  invariant balance >= 0

a = Account(owner: "Ann", balance: 5)
println(a)
b = Account(...a, balance: a.balance - 10)
println(b)
```
**The compiler says:**

```
abort in fiber main (line 8): invariant of Account failed: balance >= 0 (supplier bug)
```

The second construction would break the rule, so the program stops at the line that built the bad value.

## Contracts on interfaces

The contract of an interface member belongs to the interface, so every `impl` obeys it, and an `impl` may not add contracts of its own (that's a compile error). Generic code bounded by the interface gets the contract through it. An interface member has no body, so its signature carries the condition, and a member with no body has no default:

```moxie
interface Named
  fn name(self) String where len(result) > 0

tuple Cat deriving show
  nm String

impl Named for Cat
  fn name(self) String = self.nm

println(Cat(nm: "tom").name())
println(Cat(nm: "").name())
```
**The compiler says:**

```
abort in fiber main (line 11): postcondition failed in name: len(result) > 0 (supplier bug)
```

The first line prints `tom`; the second `Cat` breaks the interface's promise, and the failure is blamed on the supplier.

## Conditions are pure

A condition may call only pure functions (lesson 45), as `debug_assert` may. Contracts are checked in debug builds and in `moxie test`. `moxie build --release` removes them, as it removes `debug_assert`, unless the manifest sets `[contracts]` `keep_in_release = true`.

Because `moxie test` checks contracts, a property test (lesson 32) exercises them: the postconditions are the properties that its generated inputs try to break.

## Conditions on fields, and between fields

A condition about one field goes after the field, and a condition that relates several fields is an `invariant` line:

```moxie
fn abs(n Int) Int where result >= 0
  if n < 0
    0 - n
  else
    n

tuple Account deriving show
  balance Int where balance >= 0
  limit Int
  invariant limit >= 0 - balance

println(abs(-4))
println(Account(balance: 5, limit: 2))
```
**Output:**

```
4
Account(balance: 5, limit: 2)
```

`i Int where i >= 0` is a precondition, `Int where result >= 0` after the result type is a postcondition, `balance Int where balance >= 0` after a field is a condition on that field, and an `invariant` line says something about the fields together. A condition that is long can continue on the next line.

Wherever the condition is written, the blame and the build modes are the same. The checker also tries to prove a condition where it has to hold: lesson 49 shows it for a parameter at each call, and it does the same for a result at each exit and for a field wherever a value is built. What it can see is false is a compile error, and what it can neither prove nor refute is checked when the program runs, quietly for a result or a field and with a note for a parameter, unless `prove = true` asks for a proof every time. In the `abs` above, the test `n < 0` is what lets the checker see that `0 - n` is not negative.

## What to remember

- A `where` after a parameter is the caller's promise, a `where` after the result type is the function's, and `invariant` is the type's.
- A failed precondition blames the caller; a failed postcondition or `invariant` blames the supplier.
- Invariants are checked wherever a value is built.
- An interface owns the contract of its members; impls can't add their own.
- Conditions must be pure; release builds drop contracts unless the manifest keeps them.

---

[← Refined parameters: proofs in the signature](49-refined-parameters.html) · [Contents](./) · [The system around your program →](44-the-system-around-your-program.html)
