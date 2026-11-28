---
layout: default
learn: true
title: "The pyramid of doom · Moxie Mixer’s Guide"
---
# 70. The pyramid of doom

Some code gets more indented with every step. Each check opens a new level, and by the fourth or fifth step the real work is buried at the right edge of the screen. Programmers call this the *pyramid of doom*, and it usually comes from one of two things: a result that must be checked before the next step, or a chain of conditions that each need the one before. Moxie gives you three tools to keep the shape flat: `?` for results, guard clauses with `return` for conditions, and `when` for choosing among values.

## The shape of the problem

Suppose a user's city decides which shop to use, and the shop decides the zip code. Each lookup can fail, so each one has to be checked before the next runs. Written as nested matches, the code moves right at every step:

```moxie
tuple User
  id Int
  city String

tuple Shop
  city String
  zip String

fn find_user(id Int) Result[User, Error]
  if id == 1 then Ok(User(id: 1, city: "Oakland")) else fail(1, "no user $id")

fn find_shop(city String) Result[Shop, Error]
  if city == "Oakland" then Ok(Shop(city: city, zip: "94607")) else fail(2, "no shop in $city")

fn nested(id Int) Result[String, Error]
  when find_user(id)
    Err(e) -> Err(e)
    Ok(u) ->
      when find_shop(u.city)
        Err(e) -> Err(e)
        Ok(s) -> Ok("shop zip ${s.zip}")

println(nested(1))
```
**Output:**

```
Ok("shop zip 94607")
```

Each failure is passed out by hand, and each success opens another level. With three steps this is readable. With ten it isn't.

## `?` keeps the steps in a line

Put `?` after a call that returns a `Result`. If the value is an `Ok`, you get the value and the function goes on. If it is an `Err`, the function returns that `Err` at once. The same function, flat:

```moxie
tuple User
  id Int
  city String

tuple Shop
  city String
  zip String

fn find_user(id Int) Result[User, Error]
  if id == 1 then Ok(User(id: 1, city: "Oakland")) else fail(1, "no user $id")

fn find_shop(city String) Result[Shop, Error]
  if city == "Oakland" then Ok(Shop(city: city, zip: "94607")) else fail(2, "no shop in $city")

fn flat(id Int) Result[String, Error]
  u = find_user(id)?
  s = find_shop(u.city)?
  Ok("shop zip ${s.zip}")

println(flat(1))
println(flat(2))
```
**Output:**

```
Ok("shop zip 94607")
Err(Error(code: 1, message: "no user 2"))
```

Every step reads as a line of its own, the success path reads straight down, and the errors still go back to the caller. Lesson 14 explains `Result` and `?` in full.

## Guard clauses for plain conditions

When a check has no value to pass on, write it as a guard that returns early. The main path stays at the left margin:

```moxie
fn classify_size(n Int) String
  if n <= 0 then return "not positive"
  if n >= 100 then return "too big"
  if n % 2 == 0 then return "even"
  "odd"

println(classify_size(-3))
println(classify_size(7))
println(classify_size(40))
```
**Output:**

```
not positive
odd
even
```

A nested version of the same checks would open three levels and put the answers at the far right. The guard version gives one answer per line, and the last line is the default.

## `when` for choosing among values

When the question is "which of these is it?", a `when` with one arm per case is flatter than a chain of nested `if`s:

```moxie
fn size_word(n Int) String
  when n
    0 -> "none"
    1 -> "one"
    else "many"

println(size_word(0))
println(size_word(5))
```
**Output:**

```
none
many
```

## What to remember

- Use `?` when a step returns a `Result` and the next step depends on it.
- Use a guard clause with `return` when a check ends the function early.
- Use `when` when the question has several answers.
- If a function still needs a deep nest, split it into smaller functions with names, and let each one do a single check.

---

[← Call by value, reference, name, and need](70-call-by-value-reference-name-and-need.html) · [Contents](./) · [Iterators and generators →](72-iterators-and-generators.html)
