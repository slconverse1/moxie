---
layout: default
dialect: gc
learn: true
title: "Call by value, reference, name, and need · Moxie/gc Mixer’s Guide"
---
# 69. Call by value, reference, name, and need

A function receives its arguments in one of several ways, and the choice decides what the caller sees and when the work happens. The four ways have names, and moxie has all of them: *call by value* is the default, *call by reference* is the `ref` parameter, *call by name* is the `lazy` parameter, and *call by need* is a `lazy` value that is computed once. Each one is a different answer to two questions: whose variable does the function change, and how often is the argument computed?

## Call by value

The default. The argument is computed once, before the call, and the function gets its own copy. Nothing the function does can change the caller's variable.

```moxie
fn add_one(x Int) Int
  x = x + 1
  x

count Int = 1
println(add_one(count))
println(count)
```
**Output:**

```
2
1
```

The function changed its own copy. The caller's `count` is still 1.

## Call by reference

A parameter marked `ref` gives the function the caller's variable. Moxie does this by copying the value in, letting the function change it, and copying the final value back when the function returns. The caller marks the call with `ref` too, so the change is visible where the call is written.

```moxie
fn bump(ref n Int) Unit
  n = n + 1

count Int = 1
bump(ref count)
println(count)
```
**Output:**

```
2
```

Lesson 8 covers `ref` in more detail. The point here is the name: the function is given a reference to the caller's variable, not a copy of its value.

## Call by name

A parameter marked `lazy` receives the argument as an expression, not a value. The argument is computed each time the function reads the parameter, so a parameter used twice is computed twice:

```moxie
impure fn noisy(n Int) Int
  println("evaluating $n")
  n * 10

fn twice_by_name(lazy x Int) Int
  x + x

println(twice_by_name(noisy(3)))
```
**Output:**

```
evaluating 3
evaluating 3
60
```

Call by name lets a function decide whether, and how often, an argument is used. It is also the way to pass code that should run only on demand, which is why it pairs with the lazy forms in the last lesson.

## Call by need

Call by need computes a value the first time it is needed, and then keeps it. A `lazy` binding is call by need: its initializer is pure, it runs on the first read, and every later read uses the same value.

```moxie
fn read_once(d Int) Int
  lazy v = 100 / d
  v + v

println(read_once(4))
```
**Output:**

```
50
```

The division runs once, and both reads use its result. Call by name would compute it twice, and call by value would compute it before the call even if the function didn't read it.

## Comparing the four

| Way | When the argument runs | Can the function change the caller's variable? | Keyword |
|---|---|---|---|
| Call by value | once, before the call | no | (none) |
| Call by reference | once, before the call | yes | `ref` |
| Call by name | at each read | no | `lazy` parameter |
| Call by need | at the first read, once | no | `lazy` binding |

## What to remember

- The default is call by value: a copy, computed once, before the call.
- `ref` gives the function the caller's variable, and the caller writes `ref` too.
- `lazy` on a parameter is call by name: computed at each use.
- `lazy` on a binding is call by need: computed at the first use, then kept.

---

[← Eager and lazy evaluation](69-eager-and-lazy-evaluation.html) · [Contents](./) · [The pyramid of doom →](71-the-pyramid-of-doom.html)
