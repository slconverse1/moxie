---
layout: default
learn: true
title: "Byte streams: Reader and Writer · Moxie Mixer’s Guide"
---
# 63. Byte streams: Reader and Writer

<div class='specref' markdown='1'>In the Spec: [19c. Files and sockets](../spec.html#s19c)</div>

Files, sockets, standard input and output, and a buffer in memory all move bytes. The `io` package gives them two interfaces, so a function written once works on any of them. `Reader` has `read(ref self, n Int)`, which returns up to `n` bytes and an empty array at the end, and `Writer` has `write(ref self, bytes Array[Byte])`, which takes all of the bytes or gives an `Err`.

## Writing to anything

`io.say` writes text to any `Writer`. The `ref` at the call is there because writing changes the stream, in the same way that `ref` marks any call that rebinds a variable (lesson 10):

```moxie
import io

io.say(ref stdout, "hello\n")?
b = io.buffer()
io.say(ref b, "kept in memory\n")?
println(len(io.contents(b)))
```
**Output:**

```
hello
15
```

## Copying

`io.copy(ref from, ref to)` moves everything and gives the number of bytes. The two ends can be different kinds of thing:

```moxie
import io

source = io.buffer_of("one\ntwo\n")
n = io.copy(ref source, ref stdout)?
println("copied $n bytes")
```
**Output:**

```
one
two
copied 8 bytes
```

## Reading in pieces

A read returns what is left, up to `n` bytes, and `Ok` of an empty array when nothing is. Each read moves the position, which is why the call says `ref`:

```moxie
import io

b = io.buffer_of("abcde")
first = ref b.read(3)?
second = ref b.read(3)?
third = ref b.read(3)?
println("${len(first)} ${len(second)} ${len(third)}")
```
**Output:**

```
3 2 0
```

`io.read_all(ref r)` reads to the end and gives all the bytes.

A `Buffer` can also go back and move around. `ref b.rewind()` returns to the start, which is how you read what you just wrote, and `ref b.seek(n)` moves to byte `n`, kept between the start and the end. `io.position(b)` tells you how many bytes have been read:

```moxie
import io

b = io.buffer_of("abcdef")
head = ref b.read(4)?
println(io.position(b))
ref b.rewind()
again = ref b.read(2)?
println("${len(head)} ${len(again)} ${io.position(b)}")
```
**Output:**

```
4
4 2 2
```

## Your own function over any stream

Write against the interface and take the stream by `ref`:

```moxie
import io

fn banner[W io.Writer](ref w W, title String) Result[Unit, Error]
  io.say(ref w, "== ${title} ==\n")

b = io.buffer()
banner(ref b, "log")?
banner(ref stdout, "console")?
println(len(io.contents(b)))
```
**Output:**

```
== console ==
10
```

## Your own streams

Any type can join by implementing the interface. The method declares `ref self` and rebinds `self` to the updated value, as in lesson 19:

```moxie
import io

tuple Counting deriving show
  bytes Int

impl io.Writer for Counting
  fn write(ref self, data Array[Byte]) Result[Unit, Error]
    self = Counting(bytes: self.bytes + len(data))
    Ok(())

c = Counting(bytes: 0)
io.say(ref c, "twelve bytes")?
io.say(ref c, "!")?
println(c)
```
**Output:**

```
Counting(bytes: 13)
```

## What to remember

- `io.Reader` and `io.Writer` are interfaces over `Io` (files and sockets), `stdin`, `stdout`, `stderr`, and `io.Buffer`.
- Both take `ref self`, so every call is written `ref r.read(n)`, `ref w.write(bytes)`, or through a helper: `io.say`, `io.copy`, `io.read_all`.
- A read returns an empty array at the end.
- Write your own functions with a `Reader` or `Writer` bound, and your own types with `impl io.Writer for ...`.

---

[← Calling C](54-calling-c.html) · [Contents](./) · [Moxie and moxie/gc side by side →](60-the-two-dialects.html)
