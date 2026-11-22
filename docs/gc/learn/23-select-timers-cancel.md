---
layout: default
dialect: gc
title: "Waiting on several things: select, timers, and cancelling · Learning Guide moxie/gc"
---
<p><small>Concurrency</small></p>

# 29. Waiting on several things: select, timers, and cancelling

A fiber often has to wait for more than one thing: a message from a worker, or a timeout; input from one channel or another. `select` waits on several at once and runs the arm for whichever is ready.

## select

Each arm is a `read` of a channel, with the arrow and what to do. The arm that is ready runs, and `select` is an expression, so it can produce a value:

```moxie
a_rx, a_tx = Chan[String][1]()
b_rx, b_tx = Chan[Int][1]()
\write(b_tx, 7)
r = select
  msg = read(a_rx) -> "text $msg"
  n = read(b_rx) -> "number $n"
println(r)
```
**Output:**

```
number 7
```

Only the `b` channel has anything in it, so that arm runs and `n` is 7. If more than one is ready, one of them is chosen. If none is ready, `select` waits until one is, so a `select` is a place where a fiber gives way to the others.

## Don't wait: else

An `else` arm runs when nothing is ready *right now*, so the fiber never waits:

```moxie
rx, tx = Chan[Int][1]()
r = select
  v = read(rx) -> "got $v"
  else "nothing ready"
println(r)
```
**Output:**

```
nothing ready
```

This is how you poll a channel in the middle of other work.

## Timeouts

`after(d)` makes a timer that fires once after a duration, and reading it is a `select` arm. A duration is written as a number with a unit: `50ms`, `5s`, `2m`, `1h`. A timeout is a `select` between the thing you want and the timer:

```moxie
rx, tx = Chan[Int][1]()
timeout = after(50ms)
r = select
  v = read(rx) -> "got $v"
  read(timeout) -> "timed out"
println(r)
```
**Output:**

```
timed out
```

Nobody writes to the channel, so the timer wins. Make timers *before* a loop that uses them, not inside it.

`sleep(d)` pauses a fiber for a duration and lets the others run:

```moxie
println("before")
sleep(20ms)
println("after")
```
**Output:**

```
before
after
```

A duration is its own type: `5s + 500ms` is a duration, `5s * 3` is too, and `5s + 1` is a compile error, since one is a time and the other a bare number.

## Loops that run until told to stop: daemon

A `daemon` block is a loop that runs forever, or until it executes `break daemon`. It is meant for the main loop of a long-running fiber or program:

```moxie
ticks = 0
daemon
  ticks = ticks + 1
  println("tick $ticks")
  if ticks == 3
    break daemon
  sleep(10ms)
println("done")
```
**Output:**

```
tick 1
tick 2
tick 3
done
```

In moxie/gc the collector reclaims what a cycle no longer needs, so a daemon runs for ever in bounded memory without any special rule.

Here is a typical shape: wait for a message or a timeout, and leave the loop either way:

```moxie
fiber fn feed(tx ChanW[String], msg readonly String) Unit
  sleep(20ms)
  \write(tx, msg)
rx, tx = Chan[String][1]()
go feed(move tx, "hello from a fiber")
timeout = after(5s)
daemon
  select
    msg = read(rx) ->
      println("got: $msg")
      break daemon
    read(timeout) ->
      println("timed out")
      break daemon
    else
      sleep(5ms)
```
**Output:**

```
got: hello from a fiber
```

The `else` arm keeps the loop turning, checking again a moment later. (`msg` is `readonly`, a string that lives for the whole program, because a text built at run time can't be passed to a fiber that outlives the call.)

## Stopping a fiber politely: cancel

A fiber that loops forever, like a worker or a ticker, needs a way to be told to stop. A `Cancel` token is passed to the fiber like any other argument. The fiber looks at it when it is ready to, in a `select` with a `cancelled(...)` arm. Cancelling is a *request*: nothing stops a fiber in the middle of a statement, and a fiber that never looks at its token runs on.

## Waiting for fibers: wait

A `wait` block waits for every fiber started inside it before the block ends. `wait s` also names the block's own `Cancel` token, `s`, so the fibers started inside can be asked to stop:

```moxie
fiber fn worker(id Int, out ChanW[String], stop Cancel) Unit
  for true
    select
      cancelled(stop) ->
        \write(out, "worker ${id} stopping")
        return
      else
        sleep(10ms)
rx, tx = Chan[String][4]()
wait s
  go worker(1, clone(tx), s)
  go worker(2, tx, s)
  sleep(50ms)
  cancel(s)
println("wait over")
println(read(rx))
println(read(rx))
```
**Output:**

```
wait over
Ok("worker 1 stopping")
Ok("worker 2 stopping")
```

The workers spin until `cancel(s)`. Each notices on its next turn, writes a farewell, and returns. The block does not end until both have finished, so "wait over" comes after both farewells have been written, and no fiber is left running after the block.

Leaving a `wait` block early, with `?`, `return`, `break`, or `continue`, cancels its token first and then waits, so no fiber outlives the block. Reaching the end of it normally does *not* cancel anything: call `cancel(s)` yourself when a fiber would otherwise run forever.

A fiber parked in a plain `read` or `sleep` can't notice a cancel, so a fiber that has to stop promptly waits inside a `select` that has a `cancelled` arm, and uses `after(d)` for a sleep that can be cut short.

---

[← Fibers and channels](22-fibers-and-channels.html) · [Contents](./) · [Atoms and futures →](24-atoms-and-futures.html)
