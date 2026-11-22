---
layout: default
dialect: gc
title: "Testing, assertions, and checking · Learn moxie/gc"
---
<p><small>Quality and larger programs</small></p>

# 31. Testing, assertions, and checking

Moxie has testing built in: no framework to install, and nothing to import. A `test` block is code that runs only when you ask for tests. This lesson also covers the other ways moxie helps you find mistakes before users do.

## test blocks and assertions

A `test` block has a name and a body, and the body uses `assert`, `assert_eq`, and `assert_ne`:

```moxie
fn double(x Int) Int
  x * 2
test "double doubles"
  assert_eq(double(4), 8)
  assert(double(0) == 0)
  assert_ne(double(1), 3)
```
**Output:**

```
ok    double doubles
1 passed, 0 failed
```

You run tests with `python3 -m moxie test file.mxi`. Each test runs in its own fiber, one after another, and the entry file's own statements don't run. A normal `moxie run` checks the test blocks for mistakes and then ignores them, so tests cost nothing in a program you ship.

A failed assertion ends that test with a message that shows what differed, and the rest of the tests still run:

```moxie
fn double(x Int) Int
  x * 2
test "passes"
  assert_eq(double(4), 8)
test "fails"
  assert_eq(double(4), 9)
```
**Output:**

```
ok    passes
FAIL  fails: (line 6): assert_eq failed: 8 != 9
1 passed, 1 failed
```

`assert_eq(a, b)` reports both values, which is why it is better than `assert(a == b)` for finding out what went wrong. A test can use any moxie code, including functions that return `Result` (check the value with `when` or `is_ok`).

## Property tests: forall

An `assert` checks one case. A `forall` checks a rule for many values at once. Name the values and their types, and the body runs for 100 generated cases:

```moxie
test "reversing twice changes nothing"
  forall xs List[Int]
    assert_eq(xs |> reverse() |> reverse() |> collect(), xs)
```
**Output:**

```
ok    reversing twice changes nothing
1 passed, 0 failed
```

The values come from the types: whole numbers (with the edge cases mixed in), `Bool`, `Char`, `String`, `Double`, lists and arrays of those, tuples, your own tuples and enums. The run is seeded, so it repeats exactly. When a property fails, moxie *shrinks* the failing case before reporting, so you see a small example rather than a huge one, along with the seed that replays it:

```moxie
test "a wrong property"
  forall n Int
    assert(n < 1000)
```
**Output:**

```
FAIL  a wrong property: (line 2): property failed on case 5 of 100 (seed 20260101): n = 1000: assertion failed [first failure: n = 9223372036854775806]
0 passed, 1 failed
```

The report names the first value that failed (here `n = 1000`, the smallest value that breaks the rule), and the original unshrunk one. `moxie test --seed 7 file.mxi` varies the run and `--cases 1000` runs more of them. The body of a `forall` must be pure: it can't print or use files.

For your own types, a `forall` builds values from the tuple's fields, and an `invariant` on the type makes it draw again when a value is rejected. For rules too tight for that, a type can supply its own `generate`.

## Looking at values while you work: dbg

`dbg(expr)` prints an expression's value to the *error* stream, labeled with the file and line, and returns the value, so you can wrap any part of an expression:

```moxie
fn double(x Int) Int
  x * 2
total = dbg(double(2)) * 2
println(total)
```
**Output:**

```
8
```

Standard output shows only `8`: the `dbg` line went to the error stream. The compiler warns that a `dbg` was left in, so it is hard to forget. `trace("message")` is the same idea for a plain message.

## What moxie check proves

`moxie check file.mxi` reads the whole program and reports mistakes without running anything, and `moxie run` stops on the same errors before the first line executes. It follows one rule: it reports only what it can *prove*, so a value whose type it can't work out is never reported as an error. What it checks:

- **Types.** Every call, operator, index, slice, range, `if` and `when` arm, `?`, `return`, and annotation agrees with the declared types, through lambdas, pipelines, and generic functions.
- **Names and shapes.** Undefined names, unknown cases, wrong argument counts, missing or extra fields, a `when` that misses a case, a pattern that can't match.
- **What a type can do.** `==` on a tuple needs `deriving eq`, `<` needs `deriving ord`, a Dict key needs `deriving eq, hash`. Nothing is compared by accident.
- **Errors as values.** `?` needs a `Result` in a function that returns a `Result`.
- **Ownership.** Use after move, `ref` and `move` mismatches.
- **Sizes and numbers.** Array shapes, a constant index past the end, a literal that doesn't fit its type, division by a constant zero.
- **Shadowing.** A name bound in an inner block hides the outer one, and the compiler tells you when you probably meant `name@1`.
- **Effects.** What a function prints, waits on, or reaches, checked against what it says about itself.

What it leaves alone is whatever depends on a value that only exists when the program runs, such as whether a Dict key is present or which index a variable holds. Those are the places for tests.

## Formatting: moxie fmt

`moxie fmt file-or-folder` rewrites source into one layout and has no options, so a team doesn't argue about style. It fixes indentation (two spaces per level), trailing spaces, extra blank lines, and the final newline. `moxie fmt --check` changes nothing and exits with an error if a file would change, which suits a build script. Before it writes a file it verifies that the program is still the same: that the tokens match, every comment is kept, and a second run changes nothing, and it leaves the file alone if any check fails.

## Putting it together

A typical function's life: you write it with a signature, `moxie check` proves the types agree, a `test` block shows an example, a `forall` states the general rule, and `moxie fmt` keeps the layout tidy. Types catch the mistakes that a type can express, and tests catch what is left.

---

[← Session types: a channel that remembers the conversation](52-session-types.html) · [Contents](./) · [Formatting and checking: `moxie fmt` and `moxie check` →](57-formatting-and-checking.html)
