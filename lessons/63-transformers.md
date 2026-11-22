# Transformers and the mtl classes

@nogc
Monad transformers need closures of one type per signature, so they ship only with moxie/gc. In GC-free moxie, handle several effects at once with the tools in earlier lessons: `Result` and `?` for failure, a tuple threaded through a `reduce` for state, and a `mutable` block (lesson 19) for the places where in-place updates are the clearest code.
@end

@gc
A **transformer** adds one capability to any monad underneath it. `import fp.trans` gives `StateT`, `ReaderT`, `WriterT`, and `ExceptT` (each takes the inner monad as its first type argument), `Identity` for the bottom of a stack, and four classes that say what a program needs rather than which stack provides it:

- `MonadState[S]`: `get`, `put`, `modify`, `gets`
- `MonadReader[R]`: `ask`, `asks`, `local`
- `MonadWriter[W]`: `tell`, `listen`, `censor`
- `MonadError[E]`: `throw_error`, `catch_error`

The plain monads of the earlier lessons are these transformers with nothing underneath: `fp.state`'s `State[S, A]` wraps `StateT[Identity, S, A]`, and `fp.reader`, `fp.writer`, and `fp.cont` do the same with `ReaderT`, `WriterT`, and `ContT`. They keep their own names and the plain results, such as the `(result, state)` pair from `run`, so a program that needs no other effect never writes `Identity`.

## Write once, pick the stack later

You write the program once, calling the class members on `M`, and choose the stack where you call it. Here is a counter that fails when it passes a limit, run on two different stacks:

```moxie
import fp.trans

fn tick[M[_] Monad + MonadState[Int] + MonadError[String]](limit Int) M[Int]
  M.get().flat_map((n) ->
    if n >= limit then M.throw_error("too big") else M.put(n + 1)
  ).flat_map((u) -> M.get())

fn state_then_error(s Int) Result[(Int, Int), String]
  trans.run_identity(trans.run_except_t(trans.run_state_t(tick[trans.StateT[trans.ExceptT[trans.Identity, String, _], Int, _]](5), s)))
fn error_then_state(s Int) (Result[Int, String], Int)
  trans.run_identity(trans.run_state_t(trans.run_except_t(tick[trans.ExceptT[trans.StateT[trans.Identity, Int, _], String, _]](5)), s))
println("${state_then_error(1)} ${state_then_error(9)}")
println("${error_then_state(1)} ${error_then_state(9)}")
```
```output
Ok((2, 2)) Err("too big")
(Ok(2), 2) (Err("too big"), 9)
```

The same `tick` runs on both stacks, and the order of the layers decides what a failure costs: with `StateT` over `ExceptT` an error throws the state away, and with `ExceptT` over `StateT` the state survives it. Return-type polymorphism needs the type written out, so the stack goes in `[...]` at the call and `M.` does the rest inside.

A class member reaches through every layer above the one that provides it (`M.get()` works on a `ReaderT` over a `StateT`). Each transformer also has a `lift_` function (`lift_state_t`, `lift_reader_t`, `lift_writer_t`, `lift_except_t`) that runs an action of the inner monad. A stack with `Result` or `List` at the bottom works too, so `StateT[List[_], Int, _]` explores every branch.

## Continuations and free programs in a stack

`ContT` is a continuation transformer, and `MonadCont` gives any stack `M.call_cc`, which reaches through the other layers. An escape keeps the state as it was at the moment of the jump:

```moxie
import fp.trans

fn find_first[M[_] Monad + MonadCont](xs List[Int], want Int) M[Int]
  M.call_cc((leave) -> xs.reduce(M.pure(-1), (acc, x) ->
    acc.flat_map((r) -> if x == want then leave(x * 100) else M.pure(r))))
fn begin(want Int) Int
  trans.run_identity(trans.run_cont_t(find_first[trans.ContT[trans.Identity, Int, _]](List(1, 2, 3), want), (a) -> trans.Identity.pure(a)))
println("${begin(2)} ${begin(9)}")
```
```output
200 -1
```

`FreeT[F, M, A]` is a free program whose steps run in the monad `M`, and `MonadFree[F]` gives a stack `M.wrap(instruction)` to issue one. `fold_free_t(program, on_done, step)` folds a program: `on_done` receives the final value and `step` is called once per instruction, and both return actions of `M`, so an interpreter can fail or log as it goes.

Build values through `M.pure`, `M.wrap`, the class members, and the `lift_` functions, or inside a function that names its return type. A bare constructor in a lambda (`ContT(run: ...)`, `FreeT(run: ...)`) does not know its stack's types.

## Naming a stack, and lifting

A type alias can name a whole stack, so a program can run on it with one word:

```moxie
import fp.trans

type App[A] = trans.StateT[trans.ExceptT[trans.Identity, String, _], Int, A]

fn tick[M[_] Monad + MonadState[Int] + MonadError[String]](limit Int) M[Int]
  M.get().flat_map((n) ->
    if n >= limit then M.throw_error("too big") else M.put(n + 1)
  ).flat_map((u) -> M.get())
fn begin(s Int) Result[(Int, Int), String]
  trans.run_identity(trans.run_except_t(trans.run_state_t(tick[App](5), s)))
println("${begin(1)} ${begin(9)}")
up = trans.lift[[M[_], A] -> trans.StateT[M, Int, A], _, _](Ok(1))
println(trans.run_state_t(up, 7))
```
```output
Ok((2, 2)) Err("too big")
Ok((1, 7))
```

Every transformer in `fp.trans` is a `MonadTrans`, and `lift[T, _, _](m)` lifts an action of the inner monad through any of them; the `_`s are inferred from `m`. There is no generic `lift` class over transformers beyond this, because a class over constructors of constructors is something moxie leaves out, which is why each transformer also has its own `lift_` function.
@end
