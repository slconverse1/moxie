# Programs with effects as data: the freer monad

The same idea as the last lesson covers programs that *do* things. The commands are described as data, and a program is data that holds a command and what to do with its answer. A separate function, a *handler*, decides what the commands actually do. That way the same program can talk to the real world in production and to a script in a test.

This is an advanced lesson. It builds on GADTs (lesson 52) for typed commands and on monads (lesson 46).

## Commands and programs

The commands are a GADT whose result type says what each command gives back. A program is either finished (`Pure`) or a command together with a function from its answer to the rest of the program (`Bind`):

```moxie
enum Cmd[A]
  Say(text String) Cmd[Unit]
  Ask Cmd[String]
enum Prog[A]
  Pure(a A)
  Bind[X](cmd Cmd[X], k (X) -> Prog[A])

fn say(t String) Prog[Unit] = Bind(Say(t), (u) -> Pure(()))
fn ask() Prog[String] = Bind(Ask, (s) -> Pure(s))
impl Prog[A]
  fn flat_map[B](self, f (A) -> Prog[B]) Prog[B] = when self
    Pure(a) -> f(a)
    Bind(c, k) -> Bind(c, (x) -> k(x).flat_map(f))
fn exec[A](p Prog[A]) A = when p
  Pure(a) -> a
  Bind(c, k) -> when c
    Say(t) ->
      println(t)
      exec(k(()))
    Ask -> exec(k("bob"))

hello = eval
  say("name?")
  n <- ask()
  say("hi ${n}")
exec(hello)
```
```output
name?
hi bob
```

The `Bind` case has a type variable `X` that appears only in its payloads, not in its result type. That's an *existential* (lesson 52): the case hides which `X` it holds, and the typed command makes the answer's type line up with the function that receives it.

No `Functor` is needed for the commands, which is what makes this *freer* than the older *free* monad: any set of commands becomes a monad.

### The `eval` notation

`eval` builds programs like this one. Inside an `eval` block:

- `name <- step` runs a step and names its answer;
- a bare line is a step whose answer isn't wanted;
- `x = e` is an ordinary local;
- the last line is the program the block gives.

Each `<-` turns the rest of the block into the function passed to `flat_map`, so `eval` works for every type that has one (`Option`, `Result`, `State`, `Prog`). It is plain syntax, not a new kind of value.

The steps are pure like any lambda, so a step cannot print. Write `eval impure` to allow effects in the block (`eval pure` spells out the default), and write a line that is only for its effect as `\println("got ${n}")`; a `\` line is never a step. The enclosing function then has those effects, so a `pure fn` can't hold an `eval impure`.

`hello` is a value you can build, pass around, and inspect before running. `exec` is one handler; a second handler (one that collects the output, or feeds scripted answers) is another function over the same `Prog`. A new set of commands is another `Cmd` enum with its own handler; to let one program use several, make a union type of the enums and bound the helper functions with `Has` (lesson 50).

## A library for it: `fp.freer`

Writing `Prog`, `send`, and `flat_map` by hand for every program gets old, so the standard package `fp.freer` has them, generic over the command type: `Prog[C[_], A]` is a program whose commands are values of `C[X]`, `send` makes one command into a program, `done` ends one, and `Monad` is implemented, so `eval` blocks, `map`, and the rest work on it.

The commands can be one enum or a generic union type of several, and a handler is an ordinary function that matches on them. A handler that deals with *some* commands and hands the others on makes handlers compose. Here `handle_say` removes the `Say` commands (collecting what they print) and leaves a program that only asks, which `run_ask` finishes:

```moxie
import fp.freer

enum Say[A]
  Print(text String) Say[Unit]
enum Ask[A]
  Name Ask[String]
union type Cmds[A] = Say[A] | Ask[A]
union type OnlyAsk[A] = Ask[A]

fn handle_say[A](p freer.Prog[Cmds, A], acc List[String]) freer.Prog[OnlyAsk, (A, List[String])] = when p
  Pure(a) -> freer.done((a, acc))
  Bind(c, k) -> when c
    Print(t) -> handle_say(k(()), acc + List(t))
    Name -> freer.bind(Name, (x) -> handle_say(k(x), acc))

fn run_ask[A](p freer.Prog[OnlyAsk, A]) A = when p
  Pure(a) -> a
  Bind(c, k) -> when c
    Name -> run_ask(k("bob"))

hello freer.Prog[Cmds, Unit] = eval
  n <- freer.send(Name)
  freer.send(Print("hi ${n}"))

(u, out) = run_ask(handle_say(hello, List()))
println(out)
```
```output
List("hi bob")
```

A helper that should work in any language holding a command bounds its constructor parameter with `Has`: `fn say[C[_] Has[Say]](t String) freer.Prog[C, Unit] = freer.send(Print(t))` builds into `freer.Prog[Cmds, Unit]`, and `x freer.Prog[OnlyAsk, Unit] = say("hi")` is a compile error (`OnlyAsk has no Say`).

Handlers that run for a long program should be `tailrec fn`: a `tailrec fn` runs its tail calls as a loop, so a handler over twenty thousand commands takes no stack, where the same handler without `tailrec` slows down as the program deepens.

## Why bother

- The program is a value: you can build it, store it, and look at it before anything happens.
- Handlers are plain functions, so a test can supply scripted answers and collect the output instead of printing it.
- Effects are visible in the types: a program over `Ask` alone can't print.

## What to remember

- Commands are a GADT; a program is `Pure` or `Bind(command, rest)`.
- `eval` with `name <- step` is the notation; `eval impure` allows effects in the block.
- `fp.freer` gives `Prog`, `send`, `done`, and a `Monad` for any command type.
- A handler that removes some commands and passes the rest on composes with others.
