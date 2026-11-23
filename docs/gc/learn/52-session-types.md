---
layout: default
dialect: gc
learn: true
title: "Session types: a channel that remembers the conversation · Moxie/gc Mixer’s Guide"
---
# 31. Session types: a channel that remembers the conversation

<div class='specref' markdown='1'>In the Spec: [23e. Session types (the `session` package)](../spec.html#s23e)</div>

When two fibers talk in a fixed pattern ("you send a request, I send a reply"), an ordinary channel can't tell you if someone gets the order wrong. A **session** is a pair of channel ends whose *type* is the conversation, so the compiler checks that each side follows it. You write the conversation once, as a type. This lesson builds on channels and fibers (lesson 28) and uses the standard `session` package.

## A request and a reply

```moxie
import session
type Client = session.Send[Int, session.Recv[Int, session.End]]

fiber fn serve(e session.Endpoint[session.Peer[Client]]) Result[Unit, Error]
  (n, e2) = session.recv(e)?
  e3 = session.send(e2, n * 2)?
  Ok(session.finish(e3))

fn client(c session.Endpoint[Client]) Result[Int, Error]
  c2 = session.send(c, 21)?
  (r, c3) = session.recv(c2)?
  session.finish(c3)
  Ok(r)

c, s = session.connect[Client]()
go serve(move s)
println(client(c))
```
**Output:**

```
Ok(42)
```

`Client` reads "send an `Int`, then receive an `Int`, then stop". `session.connect[Client]()` gives you both ends: `c`, whose type is `Client`, and `s`, whose type is `session.Peer[Client]`, the mirror image (the other side receives where this side sends).

Each step (`send`, `recv`, `finish`) takes the endpoint you hold and gives back the endpoint for the next step, so you rebind a new name each time. Once a step is taken, the old name is used up.

That is all you need for ordinary use, and the compiler now catches mistakes that would otherwise be a hang or a crash:

- **Wrong order:** `recv` on an endpoint that should `send` first.
- **Wrong type:** sending a `String` where the conversation says `Int`.
- **Using an endpoint twice:** *use of moved value `c`*, since a step used it up.
- **Dropping the conversation:** a function that ends while the endpoint still has steps to go, or reaches `End` and never calls `finish`.
- **The wrong end:** passing the client's end to a function that expects the server's.

A step returns a `Result`, so `?` passes a failure on: if the other fiber has ended, your next step gets an `Err` instead of waiting forever. A program that never imports `session` pays nothing for any of this: the types are erased, and the endpoints are ordinary channels underneath.

Here is the wrong-order mistake:

```moxie
import session

type Client = session.Send[Int, session.Recv[Int, session.End]]

fn client(c session.Endpoint[Client]) Result[Int, Error]
  (r, c2) = session.recv(c)?
  Ok(r)

println("never runs")
```
**The compiler says:**

```
error: mismatched types: expected `session.Endpoint[session.Recv[T, S]]`, found `session.Endpoint[session.Send[Int, session.Recv[Int, session.End]]]` (in the argument for `e` of `session.recv`)
```

## Choices

`Pick[A, B]` is a turn where *you* choose between two continuations, and `Offer[A, B]` is the other side's view: it waits and finds out. You choose with `session.pick_left(e)` or `session.pick_right(e)`, and the other side takes the result of `session.offer(e)` apart with `when`. It is a `session.Branch`, whose cases `Left` and `Right` each carry the endpoint for that branch.

```moxie
import session
type Client = session.Pick[session.Send[Int, session.Send[Int, session.Recv[Int, session.End]]], session.End]

fiber fn serve(e session.Endpoint[session.Peer[Client]]) Result[Unit, Error]
  when session.offer(e)?
    session.Branch.Left(e2) ->
      (a, e3) = session.recv(e2)?
      (b, e4) = session.recv(e3)?
      e5 = session.send(e4, a + b)?
      Ok(session.finish(e5))
    session.Branch.Right(e2) -> Ok(session.finish(e2))

fn client(c session.Endpoint[Client]) Result[Int, Error]
  c2 = session.pick_left(c)?
  c3 = session.send(c2, 20)?
  c4 = session.send(c3, 22)?
  (r, c5) = session.recv(c4)?
  session.finish(c5)
  Ok(r)

c, s = session.connect[Client]()
go serve(move s)
println(client(c))
```
**Output:**

```
Ok(42)
```

Both arms of the `when` have to finish the conversation: leaving `e2` unused in either arm is the same error as above.

## A conversation that repeats

A conversation can name itself: a type alias may mention its own name for the point where it starts over.

```moxie
import session
type EchoClient = session.Pick[session.Send[Int, session.Recv[Int, EchoClient]], session.End]
type EchoServer = session.Offer[session.Recv[Int, session.Send[Int, EchoServer]], session.End]

fn serve(e session.Endpoint[EchoServer]) Result[Unit, Error]
  when session.offer(e)?
    session.Branch.Left(e2) ->
      (n, e3) = session.recv(e2)?
      e4 = session.send(e3, n * 2)?
      serve(e4)
    session.Branch.Right(e2) -> Ok(session.finish(e2))

fn ask(c session.Endpoint[EchoClient], n Int, total Int) Result[Int, Error]
  if n == 0
    c2 = session.pick_right(c)?
    session.finish(c2)
    Ok(total)
  else
    c2 = session.pick_left(c)?
    c3 = session.send(c2, n)?
    (r, c4) = session.recv(c3)?
    ask(c4, n - 1, total + r)

fiber fn server(e session.Endpoint[EchoServer]) Result[Unit, Error]
  serve(e)

c, s = session.connect[EchoClient]()
go server(move s)
println(ask(c, 3, 0))
```
**Output:**

```
Ok(12)
```

The client asks for 3, 2, and 1 to be doubled (6 + 4 + 2 = 12), then ends it.

## Handing over an endpoint

An endpoint can itself be what a step sends: `Send[Endpoint[Private], End]`. The sender gives it up, and using it afterwards is the same *use of moved value* error, so exactly one fiber holds each end at any time.

```moxie
import session
type Private = session.Send[Int, session.Recv[Int, session.End]]
type Main = session.Send[session.Endpoint[session.Peer[Private]], session.End]

fiber fn worker(e session.Endpoint[session.Peer[Main]]) Result[Unit, Error]
  (line, e2) = session.recv(e)?
  session.finish(e2)
  (n, l2) = session.recv(line)?
  l3 = session.send(l2, n + 100)?
  Ok(session.finish(l3))

mc, ms = session.connect[Main]()
pc, ps = session.connect[Private]()
go worker(move ms)
mc2 = session.send(mc, ps)?
session.finish(mc2)
pc2 = session.send(pc, 5)?
(r, pc3) = session.recv(pc2)?
session.finish(pc3)
println(r)
```
**Output:**

```
105
```

The client opens a second, private conversation, hands one end of it to the worker through the first, and then talks to the worker on it.

## Limits

- A session has exactly two ends; there are no three-party conversations.
- The type says what is sent and received, not what the values mean or how long a step may take.
- Message types are checked where the compiler can see the endpoint's type, which is wherever the type is written (a parameter, a binding from `connect`).
- A function that takes an endpoint and hands it on uses it up, so the caller needs no `move`, and `session.Left(e)` works as a pattern as well as `session.Branch.Left(e)`.
- An endpoint stored in a collection or a tuple field is not tracked.

Mistakes: forgetting `finish` at the end, using the old name after a step (write `c2 = session.send(c, 1)?` and carry on with `c2`), and passing the client's end where the server's is expected.

## What to remember

- The conversation is a type: `Send[Int, Recv[Int, End]]`.
- Every step returns the next endpoint; the old name is used up.
- `Pick` chooses, `Offer` waits and branches; a repeating conversation names itself.
- Wrong order, wrong type, a dropped conversation, and the wrong end are compile errors.

---

[← Atoms and futures](24-atoms-and-futures.html) · [Contents](./) · [Testing, assertions, and checking →](25-testing.html)
