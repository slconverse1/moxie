---
layout: default
learn: true
title: "Fibers and channels · Mixer’s Guide moxie"
---
# 28. Fibers and channels

<div class='specref' markdown='1'>In the Spec: [16. Concurrency overview](../spec.html#s16), [17. Atoms, futures, channels, timers](../spec.html#s17), [18. Fibers, loops, streams](../spec.html#s18)</div>

A program can do several things at once. In moxie the unit of concurrency is the *fiber*, a lightweight task, and fibers talk to each other through *channels*. The idea is borrowed from Go: don't share data between tasks, pass messages between them. Since moxie values never change, a message can't be altered behind the receiver's back.

Fibers take turns on one operating-system thread. They are cheap, so a program can run thousands of them, and a fiber gives way to another whenever it waits for something.

## A channel

A channel carries values of one type from one place to another. `Chan[T][n]()` makes one and gives you its two ends: the receiving end and the sending end. `n` is the capacity, how many values can wait in the channel:

```moxie
rx, tx = Chan[String][2]()
\write(tx, "a")
\write(tx, "b")
println(read(rx))
println(read(rx))
```
**Output:**

```
Ok("a")
Ok("b")
```

`write(tx, value)` sends and `read(rx)` receives. Both return a `Result`, because either can fail: a read from a channel with nothing in it and no writers left, or a write to a closed channel. The `\` at the start of `\write(...)` means "I am deliberately ignoring this result", which is how you tell the compiler you didn't forget it.

A channel's two ends have separate types, `ChanR[T]` for reading and `ChanW[T]` for writing, so a function that only reads can't write by mistake.

## Closing a channel

A sender says "no more" by closing its end. A reader sees that as an error once the channel is empty:

```moxie
rx, tx = Chan[String][2]()
\write(tx, "a")
\write(tx, "b")
close(tx)
println(read(rx))
println(read(rx))
println(read(rx))
```
**Output:**

```
Ok("a")
Ok("b")
Err(Error(code: 1, message: "channel closed"))
```

The third read gives `Err(...)` with the code `CLOSED`.

## Starting a fiber

A function that runs as its own fiber is declared `fiber fn`, and `go` starts it. The caller carries on immediately:

```moxie
fiber fn producer(out ChanW[Int], n Int) Unit
  for i in 1..n
    \write(out, i * i)
  close(out)
rx, tx = Chan[Int][4]()
go producer(move tx, 5)
for v in rx
  println("got $v")
```
**Output:**

```
got 1
got 4
got 9
got 16
got 25
```

The producer writes the first five squares, then closes the channel. The main program reads them with a `for` loop over the channel's receiving end, which ends when the channel closes. A channel with room for four values means the producer pauses when it is ahead of the reader, and carries on when the reader catches up.

`go` on an ordinary `fn` is a compile error that says so. A `fiber fn` can use `?`, which ends the fiber at the first failure, but the `Result` it returns goes nowhere, since nothing waits for it.

## Who owns a channel end?

A channel end is a *resource*: it has one owner at a time. Giving it away is written `move`, as above in `go producer(move tx, 5)`. After that, `tx` is gone from the main program, and using it would be a compile error:

```moxie
fiber fn producer(out ChanW[Int]) Unit
  \write(out, 1)
rx, tx = Chan[Int][1]()
go producer(move tx)
\write(tx, 2)
```
**The compiler says:**

```
error: use of moved value `tx` (moved at line 4)
```

Passing a resource to a function that only *uses* it lends it for the call, as `println(f, "hi")` does with a file. A function that closes it, moves it on, or returns it takes it over, and then the call says `move`. The compiler works out which is which, and tells you if you left off the `move`.


## Several senders: clone

To give several fibers a way to write to the same channel, make copies of the sending end with `clone`. The channel ends when the last sender is finished or has closed its end, so the reader keeps going until every sender is done:

```moxie
fiber fn worker(id Int, out ChanW[Int]) Unit
  \write(out, id * 10)
rx, tx = Chan[Int][3]()
go worker(1, clone(tx))
go worker(2, clone(tx))
go worker(3, move tx)
a = read(rx).get_or(0)
b = read(rx).get_or(0)
c = read(rx).get_or(0)
println(a + b + c)
```
**Output:**

```
60
```

The workers write 10, 20 and 30 in some order, and the three reads add up to 60 either way, so the program's answer doesn't depend on which fiber runs first.

## Fan-in and results

A common shape: start several fibers, each of which writes its result to a shared channel, then collect them. The loop below starts four, and the main program adds up what comes back. Reading with `for` ends when the channel is closed and empty:

```moxie
fiber fn square(n Int, out ChanW[Int]) Unit
  \write(out, n * n)
rx, tx = Chan[Int][4]()
for n in 1..3
  go square(n, clone(tx))
go square(4, move tx)
total = 0
for v in rx
  total@1 += v
println(total)
```
**Output:**

```
30
```

`clone` in a loop is allowed only because the last fiber takes the original with `move`, so no sender is left open that would keep the reader waiting forever. Squares of 1, 2, 3 and 4 add up to 30.

## Deadlock

If every fiber is waiting for something that only another waiting fiber could provide, nothing can ever proceed. Moxie detects this and stops the program with a message, rather than hanging:

```moxie
rx, tx = Chan[Int][1]()
println(read(rx))
```
**The compiler says:**

```
deadlock: every fiber is waiting and nothing can wake them
```

Here the only fiber waits to read a channel that nobody will ever write to (the sending end is still open, but no fiber holds it who could write).

## Limiting how many

`fiber[n] fn` limits how many copies of a fiber may be alive at once. `go` waits for a free slot when all `n` are busy, which is a simple way to bound the load; `try_go` never waits, and tells you with `Err(NO_SLOT)` that no slot was free:

```moxie
fiber[1] fn slow(n Int, out ChanW[Int]) Unit
  sleep(20ms)
  \write(out, n)
rx, tx = Chan[Int][4]()
go slow(1, clone(tx))
when try_go slow(2, clone(tx))
  Ok(_) -> println("2 started")
  Err(e) -> println("2 would have to wait")
go slow(2, move tx)
println(read(rx))
println(read(rx))
```
**Output:**

```
2 would have to wait
Ok(1)
Ok(2)
```

The first `go` takes the only slot, so `try_go` is refused. The last `go` waits about twenty milliseconds for the slot and then runs.

## Why this design

Because values never change and channel ends have a single owner, a moxie program has no data races to reason about. Two fibers can only affect each other by sending a message, and every message is a value. The next lessons add the tools for waiting on several things at once, for shared counters, and for stopping a fiber.

---

[← Pipe slots, `seq`, and doing work once](50-pipe-slots-and-caching.html) · [Contents](./) · [Waiting on several things: select, timers, and cancelling →](23-select-timers-cancel.html)
