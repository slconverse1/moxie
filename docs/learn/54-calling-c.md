---
layout: default
learn: true
title: "Calling C · Learning Guide moxie"
---
<p><small>Your program and its machine</small></p>

# 62. Calling C

Most programs never need this lesson. When one does, a library written in C already exists and rewriting it would be a waste, so moxie lets you declare its functions and call them. Because the compiler can't look inside C, a foreign declaration is something *you* promise, and the rest of the language keeps its checks around it.

## Declaring C functions

A `foreign` block declares C functions by signature. Every function says what it does to the world (`pure`, `prints`, `parks`, or `impure`), because the compiler can't see inside C. After that it's called like any function:

```moxie
foreign "m"
  pure fn cos(x Double) Double
  pure fn pow(x Double, y Double) Double

println(cos(0.0))
println(pow(2.0, 10.0))
```
**Output:**

```
1.0
1024.0
```

The string names the library (`"m"` is the math library, `"c"` the C library). The program needs the `ffi` permission (lesson 61).

## Out-parameters

A `ref` parameter is a C out-parameter: the value goes in, and the result is copied back when the call returns:

```moxie
foreign "m"
  pure fn frexp(x Double, ref exp Int32) Double

e = 0i32
m = frexp(8.0, ref e)
println("${m} ${e}")
```
**Output:**

```
0.5 4
```

## Arrays and callbacks

An `Array` of any number type is passed as a pointer. A parameter written `n UInt = len(base)` is C's length, filled in by the call, and `size UInt = size_of(base)` is the element size. A parameter of function type is a C callback for the length of the call, and `Ptr[T]` in the callback's type is a `const T *` that arrives as the value. That is enough to declare `qsort` and call it with a closure:

```moxie
foreign "c"
  impure fn qsort(
    ref base Array[Int32],
    n UInt = len(base),
    size UInt = size_of(base),
    cmp (Ptr[Int32], Ptr[Int32]) -> Int32
  )

xs = Array(5i32, 3i32, 9i32, 1i32, 7i32)
qsort(ref xs, (a, b) -> a - b)
println(xs)
```
**Output:**

```
Array(1, 3, 5, 7, 9)
```

## Text

Text crosses as a `CString`, made by `cstr(text)`. The usual habit is to keep the raw declaration to yourself and export a wrapper that speaks moxie:

```moxie
foreign "c"
  pure fn strlen(s CString) UInt

fn byte_length(text String) UInt = strlen(cstr(text))

println(byte_length("héllo"))
```
**Output:**

```
6
```

The answer is 6, because `é` is two bytes in UTF-8.

## Handles

A library that hands back an opaque pointer, such as a database, is declared as a **handle**, with the function that closes it. A handle is a resource: move-only, closed once, and the compiler rejects use after the close. A handle counts in the pool tally too (lesson 35). A function that returns `Result[Store, Error]` gives `Err(MISSING)` when C returns NULL.

This needs a library to call, so it is shown but not run:

```moxie
foreign "store"
  handle Store closes store_close
  impure fn store_open(path CString) Result[Store, Error]
  impure fn store_get(s Store, key CString) Int32
  impure fn store_close(s Store)

s = store_open(cstr("data.db"))?
println(store_get(s, cstr("answer")))
store_close(move s)
```

## Callbacks that C keeps

A callback that C **keeps** and calls later, perhaps from a thread of its own, can't run moxie code on that thread, so it becomes a message: declare `cb Events[Int32]` and pass the write end of a channel with `move`, and a fiber reads the events with `read`.

If C needs an **answer** from the kept callback, declare `cb Handler[(Int32) -> Int32]` and pass a function. When C calls from its own thread, the function runs in a fiber of its own (it may sleep or read), and the C thread waits for the result. A foreign function that waits for such a thread must be declared `parks`:

```moxie
foreign "sensor"
  impure fn on_reading(cb Events[(Int32, Double)])
  impure fn on_query(cb Handler[(Int32) -> Int32])

rx, tx = Chan[(Int32, Double)][16]()
on_reading(move tx)
on_query((id) -> id * 2i32)
for i in 1..3
  println(read(rx)?)
```

## Generating the declarations

`moxie bindgen` writes the declarations from a C header, so nobody types them by hand. `--wrap` also writes default wrappers (a `String` for each `CString`, a `Result` for the common `int` status with out-parameters), and `bindgen.toml` holds the corrections:

```
$ moxie bindgen sensor.h --package sensorx --lib sensor --wrap
```

```moxie
[functions.sensor_subscribe]
keeps = ["cb"]
```

## Safety and packages

A declaration that doesn't match the real C signature (an `Int32` where C takes a `Double`) is not detected, because the compiler can't see C. Wrap every foreign call and test the wrapper.

A package may contain `foreign` blocks only when its manifest has a `[native]` section, which lists the libraries it may name and where to look for them:

```moxie
[native]
libs = ["z"]
paths = ["native"]
```

A missing section, or a library the section doesn't list, is a compile-time error that says what to add. Granting `ffi` runs native code with all the rights of the process, so permissions guard against mistakes in moxie code, not against hostile C.

## What to remember

- `foreign "lib"` declares C functions; each one says `pure`, `prints`, `parks`, or `impure`.
- `ref` is an out-parameter; arrays pass as pointers; `n UInt = len(base)` fills in a length.
- `cstr(text)` makes a `CString`; keep raw declarations private and export wrappers.
- A `handle` is a move-only resource with a closing function.
- A callback that C keeps becomes a channel (`Events`) or a handler fiber (`Handler`).

*In the Spec: [19a. Foreign functions and `moxie bindgen`](../spec.html#s19a)*

---

[← The system around your program](44-the-system-around-your-program.html) · [Contents](./) · [Byte streams: Reader and Writer →](65-byte-streams.html)
