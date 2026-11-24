---
layout: default
dialect: gc
learn: true
title: "Errors in larger programs · Moxie/gc Mixer’s Guide"
---
# 35. Errors in larger programs

In the Spec: [15. Errors and Results](../spec.html#s15)
{: .specref}

The lesson on `Option` and `Result` covered the basics: a function that can fail returns a `Result`, and `?` passes a failure along. This lesson is about what changes when a program has many functions and several kinds of failure.

## Your own error types

`Error` has a code and a message, which is enough when a person will read it. When *code* needs to decide what to do, make the error an enum, so the compiler checks that every case is handled:

```moxie
enum ParseError deriving show
  Empty
  BadDigit(ch Char)
fn parse_digit(text String) Result[Int, ParseError]
  if text == ""
    Err(Empty)
  elif text == "x"
    Err(BadDigit(ch: 'x'))
  else
    Ok(1)
for t in List("7", "", "x")
  when parse_digit(t)
    Ok(n) -> println("digit $n")
    Err(Empty) -> println("nothing to parse")
    Err(BadDigit(c)) -> println("not a digit: $c")
```
**Output:**

```
digit 1
nothing to parse
not a digit: x
```

The `when` on the result must cover `Ok` and every `Err` case, so adding a new case to `ParseError` finds every place that needs to learn about it.

## Combining error types: From

A function that calls two others, which fail in different ways, has to return one error type. An `impl From[...] for ...` says how to convert one into another, and `?` applies it automatically, one hop:

```moxie
enum ParseError deriving show
  Empty
  BadDigit(ch Char)
enum AppError deriving show
  Parse(why ParseError)
  TooOld(limit Int)
impl From[ParseError] for AppError
  static fn from(e ParseError) AppError
    Parse(why: e)
fn parse_age(text String) Result[Int, ParseError]
  if text == "" then Err(Empty) elif text == "ancient" then Ok(150) else Ok(30)
fn check_age(text String) Result[Int, AppError]
  age = parse_age(text)?
  if age > 99 then Err(TooOld(limit: 99)) else Ok(age)
for t in List("30", "", "ancient")
  when check_age(t)
    Ok(a) -> println("age $a")
    Err(e) -> println("$e")
```
**Output:**

```
age 30
AppError.Parse(ParseError.Empty)
AppError.TooOld(99)
```

In `check_age`, `parse_age(text)?` has the error type `ParseError`, so the compiler wraps it with `AppError.from` before returning. When both error types are the same, nothing is converted. With no `From` impl, it is a compile error. The compiler won't chain two conversions, so the path from one error type to another must be a single `From`.

## Handling an error where it happens: else Err(e)

`?` hands the failure upward. To deal with it on the spot, a let-else can name the failure with a pattern of its own, so its parts are in scope. This is how to log an error, use its code, or turn it into a different error:

```moxie
fn half(text String) Result[Int, Error]
  Ok(n) = read[Int](text) else Err(e) -> Err(Error(code: 7, message: "bad number: ${e.message}"))
  Ok(n / 2)
println(half("10"))
println(half("ten"))
```
**Output:**

```
Ok(5)
Err(Error(code: 7, message: "bad number: cannot read"))
```

The two patterns must cover every shape of the value between them, so `Err(e)` here is the only thing left once `Ok(n)` fails to match.

## Many things at once: traverse and validate

To apply a function that can fail to every element of a collection, `traverse` stops at the first failure, which is right for a pipeline. `validate` runs it on every element and gives either all the results or *all* the errors, which is right for a form where you want every problem at once:

```moxie
fn check(n Int) Result[Int, String]
  when n > 0
    true -> Ok(n)
    false -> Err("bad $n")
println(traverse(check, List(5, 20, 7)))
println(traverse(check, List(5, -1, -3)))
println(validate(check, List(5, -1, 7, -3)))
```
**Output:**

```
Ok(List(5, 20, 7))
Err("bad -1")
Err(List("bad -1", "bad -3"))
```

`partition_results` splits a stream of results into the good values and the errors, and keeps going either way. `recover(r, f)` turns an `Err` into an `Ok` with a fallback computed from the error:

```moxie
fn check(n Int) Result[Int, String]
  when n > 0
    true -> Ok(n)
    false -> Err("bad $n")
(good, bad) = partition_results(List(5, -1, 7, -3) |> map(check) |> collect())
println("$good $bad")
println(recover(check(-2), (e) -> 0))
```
**Output:**

```
List(5, 7) List("bad -1", "bad -3")
Ok(0)
```

`sequence` turns a list of `Result`s into a `Result` of a list (stopping at the first `Err`), and `traverse(f, xs)` is `sequence` of `map(f)`.

## Trying again

`retry(n, delay, f)` calls `f` once, and calls it again only if it failed, waiting `delay` between tries, for up to `n` tries in all. It doesn't repeat an error that a second try can't change, such as `NOT_FOUND` or `DENIED`:

```moxie
tries = Atom[Int](0)
fn flaky() Result[Int, String]
  k = swap(tries, _ + 1)
  when k < 3
    true -> Err("not yet")
    false -> Ok(k)
println(retry(5, 1ms, flaky))
println(@tries)
```
**Output:**

```
Ok(3)
3
```

Use `retry` for calls that are safe to repeat, such as reads and connections. A call that half-worked will half-work again.

## Errors at the top of the program

In the entry file, `?` on an `Err` prints the error's message and ends the program with a non-zero exit status, so a small program doesn't need to match on every `Result` in its main flow. This one prints `24`, then fails at the second read:

```moxie
n = read[Int]("12")?
println(n * 2)
m = read[Int]("oops")?
println("never reached")
```
**The compiler says:**

```
MISSING: cannot read
```

## Aborts are for bugs

An index out of range, an arithmetic overflow, a division by zero, a failed assertion, or a `todo` aborts the running fiber with a diagnostic. These are not `Result`s on purpose. If a function can fail on *valid* input, it returns a `Result`. If it fails only because the caller did something that should never happen, it aborts, and the fix is in the caller.

## Rules of thumb

| Situation | Use |
|---|---|
| a value that may be absent, with nothing to explain | `Option` |
| an operation that can fail and the caller should hear why | `Result[T, Error]` |
| callers must react differently to different failures | your own enum as the error type |
| several fallible functions with different errors | `From` and `?` |
| a form with many fields | `validate` |
| a caller's bug | an abort, not a `Result` |

---

[← Formatting and checking: `moxie fmt` and `moxie check`](57-formatting-and-checking.html) · [Contents](./) · [Limits, pools, and the memory budget →](53-limits-pools-memory.html)
