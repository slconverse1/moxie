---
layout: default
dialect: gc
learn: true
title: "Reader, writer, and continuations · Learning Guide moxie/gc"
---
<p><small>Functional programming</small></p>

# 53. Reader, writer, and continuations


Lesson 46 introduced the `Monad` interface and what `flat_map` means. Three packages in moxie/gc give you ready-made monads for common jobs: a **Reader** (every step can read a shared setting), a **Writer** (every step can add to a log), and a **continuation** monad (a step can jump out early). The free monad is covered in lesson 51. They need closures with one type per signature, so GC-free moxie does not have them. Each is the matching transformer from lesson 54 with nothing underneath, `Identity`, so a program that later needs two effects at once can move to the transformer without relearning anything.

## Reader

`import fp.reader` gives you `asks(f)`, which builds a step that reads the environment through `f`, and `run_reader(step, env)`, which runs it with a given environment:

```moxie
import fp.reader

greet = reader.asks((n String) -> "hi ${n}")
  .flat_map((g) -> reader.asks((n String) -> "${g}!"))
println(reader.run_reader(greet, "bo"))
```
**Output:**

```
hi bo!
```

Both steps read the same name, and neither takes it as a parameter. Run the same `greet` with another environment and you get another result, with no change to `greet`.

## Writer

`import fp.writer` gives you `tell(entry)`, which adds one entry to the log, and `run_writer(step)`, which returns the value together with the whole log:

```moxie
import fp.writer

log = writer.tell("start")
  .flat_map((u) -> writer.tell("end"))
  .map((u) -> 7)
println(writer.run_writer(log))
```
**Output:**

```
(7, List("start", "end"))
```

The log is an ordinary `List`, so it is an immutable value like any other, and each step's entries are appended in order.

## Continuations

`import fp.cont` gives you a continuation monad. `call_cc` hands its function an escape: calling `leave` abandons the rest of that function and carries on from the place where `call_cc` was:

```moxie
import fp.cont

safe_div = (a Int, b Int) -> cont.call_cc((leave) ->
  if b == 0 then leave(-1) else cont.Cont.pure(a / b))
println("${cont.eval_cont(safe_div(10, 2))} ${cont.eval_cont(safe_div(1, 0))}")
```
**Output:**

```
5 -1
```

Most programs reach for `?` or `break(value)` before this, since they do the same job in plain code. Continuations earn their place when a generic function written for any monad needs an early exit (see the next lesson).

---

[← GADTs and typestate](43-gadts-and-typestate.html) · [Contents](./) · [Transformers and the mtl classes →](63-transformers.html)
