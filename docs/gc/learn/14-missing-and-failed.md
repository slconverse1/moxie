---
layout: default
dialect: gc
learn: true
title: "Missing values and failures: Option and Result · Learner’s Guide moxie/gc"
---
<p><small>Data</small></p>

# 16. Missing values and failures: Option and Result

Some operations don't always have an answer. Looking up a name that isn't there, reading a number from text that isn't a number, opening a file that doesn't exist. Many languages answer with a special value (`null`) or an exception. Moxie has neither. A function that might not produce a value says so in its *type*, and the compiler makes the caller deal with it.

There are two types for this, both ordinary enums that come with the language.

## Option: a value, or nothing

`Option[T]` is either `Some(value)` or `None`:

```moxie
fn half(n Int) Option[Int]
  if n % 2 == 0 then Some(n / 2) else None
println(half(10))
println(half(7))
```
**Output:**

```
Some(5)
None
```

To use the value inside, take it apart with `when`. It must cover both cases, so you can't forget the `None`:

```moxie
fn half(n Int) Option[Int]
  if n % 2 == 0 then Some(n / 2) else None
when half(10)
  Some(v) -> println("half is $v")
  None -> println("odd, no half")
```
**Output:**

```
half is 5
```

When you just want a fallback, `get_or` supplies one:

```moxie
fn half(n Int) Option[Int]
  if n % 2 == 0 then Some(n / 2) else None
println(half(10).get_or(-1))
println(half(7).get_or(-1))
println(is_some(half(10)))
println(is_none(half(7)))
```
**Output:**

```
5
-1
true
true
```

There is no way to treat an `Option[Int]` as an `Int` by accident. `half(7) + 1` doesn't compile. That is the whole point: the missing case can't be forgotten, so nothing is "null" at run time.

## Result: a value, or an error

`Result[T, E]` is either `Ok(value)` or `Err(error)`. It is for operations that can *fail*, where the caller should hear *why*. The usual error type is `Error`, a built-in tuple with a numeric `code` and a `message`. `fail(code, message)` makes an `Err`:

```moxie
fn safe_div(a Int, b Int) Result[Int, Error]
  if b == 0
    fail(1, "division by zero")
  else
    Ok(a / b)
println(safe_div(10, 2))
println(safe_div(10, 0))
```
**Output:**

```
Ok(5)
Err(Error(code: 1, message: "division by zero"))
```

You take a `Result` apart with `when`, exactly like an `Option`:

```moxie
fn safe_div(a Int, b Int) Result[Int, Error]
  if b == 0
    fail(1, "division by zero")
  else
    Ok(a / b)
for b in List(2, 0)
  when safe_div(10, b)
    Ok(q) -> println("quotient $q")
    Err(e) -> println("failed: ${e.message} (code ${e.code})")
```
**Output:**

```
quotient 5
failed: division by zero (code 1)
```

A lot of the language returns `Result`: reading a number from text, the file functions, the network. You met one in the lesson on text:

```moxie
println(read[Int]("42"))
println(read[Int]("forty-two"))
```
**Output:**

```
Ok(42)
Err(Error(code: 4, message: "cannot read"))
```

## Passing the failure along: ?

In a function that itself returns a `Result`, putting `?` after a call says "if this failed, return that failure from *my* function right now; otherwise give me the value". It removes the plumbing from code that does several fallible steps in a row:

```moxie
fn safe_div(a Int, b Int) Result[Int, Error]
  if b == 0 then fail(1, "division by zero") else Ok(a / b)
fn ratio_sum(a Int, b Int, c Int) Result[Int, Error]
  x = safe_div(a, b)?
  y = safe_div(a, c)?
  Ok(x + y)
println(ratio_sum(100, 5, 10))
println(ratio_sum(100, 0, 10))
println(ratio_sum(100, 5, 0))
```
**Output:**

```
Ok(30)
Err(Error(code: 1, message: "division by zero"))
Err(Error(code: 1, message: "division by zero"))
```

Whichever call fails first ends the function with its error. `?` works on `Option` the same way: it gives the value of a `Some`, or returns `None`.

```moxie
fn half(n Int) Option[Int]
  if n % 2 == 0 then Some(n / 2) else None
fn quarter(n Int) Option[Int]
  h = half(n)?
  half(h)
println(quarter(8))
println(quarter(6))
println(quarter(3))
```
**Output:**

```
Some(2)
None
None
```

The function using `?` must return the same kind: `?` on an `Option` in a function that returns a `Result` is an error, since nothing is converted silently.

## else: a way out at the call site

When you want the value or a default action, and not to hand the failure up, a *let-else* does it. If the pattern on the left matches, the names are bound. If not, the `else` value is what the whole function returns:

```moxie
fn first_word_length(text String) Int
  Some((word, _)) = split_once(text, " ") else 0
  len(word)
println(first_word_length("hello world"))
println(first_word_length("single"))
```
**Output:**

```
5
0
```

## Chaining without unpacking

Often you want to apply a function to the value inside, if there is one. `|>>` (called *bind*) feeds an `Ok` or a `Some` to a function that returns another `Result` or `Option`, and passes a failure straight through:

```moxie
fn half(n Int) Option[Int]
  if n % 2 == 0 then Some(n / 2) else None
println(Some(20) |>> half |>> half)
println(Some(10) |>> half |>> half)
println(None |>> half)
```
**Output:**

```
Some(5)
None
None
```

`map_ok` and `map_err` change the inside of an `Ok` or an `Err` without leaving the `Result`, and `is_ok` and `is_err` ask which it is:

```moxie
r = read[Int]("20")
println(map_ok(r, (v) -> v + 1))
println(is_ok(r))
println(is_err(read[Int]("x")))
println(get_or(read[Int]("x"), 0))
```
**Output:**

```
Ok(21)
true
true
0
```

## Your own error types

`Error` is convenient. When callers need to react to *which* error it was, make an enum of your own and use it as the error type:

```moxie
enum ParseError deriving show
  Empty
  BadChar(ch Char)
fn check(text String) Result[String, ParseError]
  if text == ""
    Err(Empty)
  elif contains(text, "x")
    Err(BadChar(ch: 'x'))
  else
    Ok(text)
for t in List("12", "", "1x")
  when check(t)
    Ok(v) -> println("ok $v")
    Err(Empty) -> println("nothing to check")
    Err(BadChar(c)) -> println("bad character $c")
```
**Output:**

```
ok 12
nothing to check
bad character x
```

When one function combines several error types, an `impl From[...] for ...` says how to convert one into another, and `?` applies it for you. The lesson on errors in larger programs shows that.

## Option or Result?

Use `Option` when absence is ordinary and needs no explanation: a lookup that may not find anything. Use `Result` when the operation *failed* and the caller should hear about it. The standard library returns `Result` for anything that can fail, such as reading, parsing, and the network, and `Option` is for your own code and new libraries.

## No exceptions

A fault that can't be recovered, such as an index past the end of an array, an arithmetic overflow, or a failed `assert`, *aborts* the running fiber with a diagnostic instead. That is reserved for bugs, not for conditions a program should expect. A function that can fail on valid input returns a `Result`.

*In the Spec: [15. Errors and Results](../spec.html#s15)*

---

[← Enums](13-enums.html) · [Contents](./) · [Lists →](15-lists.html)
