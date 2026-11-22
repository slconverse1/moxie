---
layout: default
dialect: gc
title: "Contracts: requires, ensures, invariant · Learning Guide moxie/gc"
---
<p><small>Fields and promises</small></p>

# 57. Contracts: requires, ensures, invariant

A contract states what a function needs and what it promises, in the code and not in a comment. It is for faults that are *bugs*: an expected failure, such as a missing file, still returns a `Result` (lesson 16). A contract failure ends the program with a message that says whose fault it was.

- `requires` is a **precondition** that the caller must meet.
- `ensures` is a **postcondition** that the function guarantees.
- `invariant` is a condition that every value of a tuple type must satisfy.

## `requires` and `ensures`

A function body may begin with `requires` and `ensures` lines, one condition per line. An `ensures` condition may name `result`:

```moxie
fn inc(x Int) Int
  requires x > 0
  ensures result > x
  x + 1

println(inc(1))
```
**Output:**

```
2
```

Arguments never change, so an `ensures` can also refer to the arguments as they were. There is no `old`. For a `ref` parameter it sees the final value.

### Who is to blame

A call checks the `requires` conditions, runs the body, checks the invariants of any value it built, and then checks the `ensures` conditions. A failed `requires` is a **caller bug**, and a failed `invariant` or `ensures` is a **supplier bug**. The message says which, and names the condition, the function, and the line:

```moxie
fn inc(x Int) Int
  requires x > 0
  ensures result > x
  x + 1

z = 0
println(inc(z))
```
**The compiler says:**

```
abort in fiber main (line 7): requires failed in inc: x > 0 (caller bug)
```

Here the function was given a value it said it couldn't take. When the *function* is wrong, it's an `ensures` that fails:

```moxie
fn bad(x Int) Int
  ensures result > x
  x - 1

println(bad(5))
```
**The compiler says:**

```
abort in fiber main (line 5): ensures failed in bad: result > x (supplier bug)
```

A `requires` whose arguments are all constants and that fails is a compile error, as a constant index out of range is:

```moxie
fn inc(x Int) Int
  requires x > 0
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

The contract of an interface member belongs to the interface, so every `impl` obeys it, and an `impl` may not add contracts of its own (that's a compile error). Generic code bounded by the interface gets the contract through it. The contract lines go in the member's block, and a member with no body has no default:

```moxie
interface Named
  fn name(self) String
    ensures len(result) > 0

tuple Cat deriving show
  nm String

impl Named for Cat
  fn name(self) String = self.nm

println(Cat(nm: "tom").name())
println(Cat(nm: "").name())
```
**The compiler says:**

```
abort in fiber main (line 12): ensures failed in name: len(result) > 0 (supplier bug)
```

The first line prints `tom`; the second `Cat` breaks the interface's promise, and the failure is blamed on the supplier.

## Conditions are pure

A condition may call only pure functions (lesson 44), as `debug_assert` may. Contracts are checked in debug builds and in `moxie test`. `moxie build --release` removes them, as it removes `debug_assert`, unless the manifest sets `[contracts]` `keep_in_release = true`.

Because `moxie test` checks contracts, a property test (lesson 31) exercises them: the `ensures` lines are the properties that its generated inputs try to break.

## Contracts or refined parameters?

Lesson 56 showed `where` on a parameter, which is *proved* at compile time. A `requires` is checked at run time (or at compile time only when the arguments are constants). Use a refined parameter when the condition is about integers and lengths and you want the compiler to insist; use a contract for anything else, including conditions on results (`ensures`) and on values you build (`invariant`).

## What to remember

- `requires` is the caller's promise, `ensures` is the function's, `invariant` is the type's.
- A failed `requires` blames the caller; a failed `ensures` or `invariant` blames the supplier.
- Invariants are checked wherever a value is built.
- An interface owns the contract of its members; impls can't add their own.
- Conditions must be pure; release builds drop contracts unless the manifest keeps them.

---

[← Refined parameters: proofs in the signature](49-refined-parameters.html) · [Contents](./) · [The system around your program →](44-the-system-around-your-program.html)
