---
layout: default
dialect: gc
learn: true
title: "Atoms and futures · Moxie/gc Mixer’s Guide"
---
# 31. Atoms and futures

In the Spec: [17. Atoms, futures, channels, timers](../spec.html#s17)
{: .specref}

Channels send messages. Two other tools cover the rest of what concurrent programs need: an *atom* is a single shared value that fibers can read and update safely, and a *future* is a value that will be available later.

## Atoms: a shared value

An `Atom` holds one value. `@` reads it, `swap` updates it by applying a function to the old value, and `reset` replaces it:

```moxie
counter = Atom[Int](0)
\swap(counter, _ + 1)
\swap(counter, _ + 1)
println(@counter)
```
**Output:**

```
2
```

An atom is the one kind of shared, changeable thing in moxie. It is safe because the update is a single step: `swap` takes the old value and a *pure* function, stores the new value, and returns it. The function must not wait or have effects, so nothing else can slip in between reading the old value and writing the new one.

`swap` returns the new value, and extra arguments go in with a placeholder call:

```moxie
fn add(x Int, y Int) Int = x + y
hits = Atom[Int](0)
a = swap(hits, _ + 1)
b = swap(hits, add(_, 5))
println("$a $b ${@hits}")
```
**Output:**

```
1 6 6
```

An atom can be shared between fibers, which is what makes it useful for a counter that several workers bump:

```moxie
fiber fn worker(n Int, total Atom[Int], done ChanW[Int]) Unit
  \swap(total, _ + n)
  \write(done, n)
total = Atom[Int](0)
rx, tx = Chan[Int][4]()
for n in 1..3
  go worker(n, total, clone(tx))
go worker(4, total, move tx)
for v in rx
  println("worker $v finished")
println(@total)
```
**Output:**

```
worker 1 finished
worker 2 finished
worker 3 finished
worker 4 finished
10
```

The order of the "finished" lines can vary from one run to the next. The final total never does: 1 + 2 + 3 + 4 is 10, however the fibers interleave.

## Guarding an atom

Give an atom a `valid:` function and every new value is checked before it is stored. A value that fails the check ends the fiber with a message and leaves the atom as it was, since breaking the rule is a bug. When rejection is an expected outcome, `try_swap` and `try_reset` give back a `Result`:

```moxie
level = Atom[Int](0, valid: (n) -> n in 0..100)
println(swap(level, _ + 30))
println(try_swap(level, _ + 90))
println(try_reset(level, 50))
println(@level)
```
**Output:**

```
30
Err(Error(code: 6, message: "rejected by the Atom's valid check"))
Ok(50)
50
```

## Watching an atom

`on_change(atom, handler)` calls `handler(old, new)` after any write that changes the value:

```moxie
fn note(old Int, new Int) Unit
  println("$old -> $new")
level = Atom[Int](0)
tok = on_change(level, note)
\swap(level, _ + 30)
\reset(level, 30)
\swap(level, _ + 5)
off_change(level, tok)
\reset(level, 0)
println(@level)
```
**Output:**

```
0 -> 30
30 -> 35
0
```

Writing the same value again is silent: `reset(level, 30)` above changed nothing, so it printed nothing. `off_change` stops the watching.

## Futures: a value that arrives later

A `Future` is a pair of ends, like a channel, but it carries *one* value, once. The writing end `resolves` it (or `rejects` it with an error), and the reading end can look at its state:

```moxie
r, w = Future[Int]()
resolve(w, 42)
when @r
  Pending -> println("waiting")
  Resolved(v) -> println("answer $v")
  Rejected(e) -> println(e.message)
```
**Output:**

```
answer 42
```

The reading end's type is `FutureR[Int]` and the writing end's is `FutureW[Int]`. `@r` reads the state without waiting: it is `Pending` until something resolves or rejects it, and then it stays that way for ever.

A future is the natural way to hand a fiber the job of computing one answer:

```moxie
fiber fn compute(n Int, out FutureW[Int]) Unit
  resolve(out, n * n)
r, w = Future[Int]()
go compute(12, move w)
sleep(20ms)
when @r
  Pending -> println("still working")
  Resolved(v) -> println("result $v")
  Rejected(e) -> println(e.message)
```
**Output:**

```
result 144
```

## Which to use

| You want | Use |
|---|---|
| a stream of messages between fibers | `Chan` |
| one answer, computed elsewhere | `Future` |
| a counter or setting several fibers share | `Atom` |
| to wait for the first of several events | `select` |

---

[← Waiting on several things: select, timers, and cancelling](23-select-timers-cancel.html) · [Contents](./) · [Session types: a channel that remembers the conversation →](52-session-types.html)
