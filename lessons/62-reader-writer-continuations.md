# Reader, writer, and continuations

@nogc
The monads in this lesson and the next are packages that need closures of one type per signature, which GC-free moxie does not have, so they ship only with moxie/gc. The idea of each, and what to use instead, is below.

- **Reader** passes a read-only setting to every step. In GC-free moxie, pass the setting as a parameter, or use a receiver block (lesson 55).
- **Writer** collects a log alongside a result. Return a tuple `(value, log)`, or build the log with a `reduce`.
- **Continuations** let a computation jump out early. Use `break(value)` in a loop, a `?` that returns an `Err`, or a `when` that returns early.

Lesson 46 and lesson 49 cover the monads that do exist in GC-free moxie.
@end

@gc
Lesson 46 introduced the `Monad` interface and what `flat_map` means. Four packages in moxie/gc give you ready-made monads for common jobs: a **Reader** (every step can read a shared setting), a **Writer** (every step can add to a log), a **continuation** monad (a step can jump out early), and the free monad (lesson 51). This lesson covers the first three. They need closures with one type per signature, so GC-free moxie does not have them.

## Reader

`import fp.reader` gives you `asks(f)`, which builds a step that reads the environment through `f`, and `run_reader(step, env)`, which runs it with a given environment:

```moxie
import fp.reader

greet = reader.asks((n String) -> "hi ${n}")
  .flat_map((g) -> reader.asks((n String) -> "${g}!"))
println(reader.run_reader(greet, "bo"))
```
```output
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
```output
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
```output
5 -1
```

Most programs reach for `?` or `break(value)` before this, since they do the same job in plain code. Continuations earn their place when a generic function written for any monad needs an early exit (see the next lesson).
@end
