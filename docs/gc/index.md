---
layout: default
dialect: gc
title: "moxie/gc"
---
<div class="dialect" markdown="1">
This is **moxie/gc**, the garbage-collected language. Prefer no collector? Visit [moxie](../), its own site with its own Tutorial, Guide, and Spec. The two are kept apart on purpose, because they make different promises.
</div>

# Hello, mixers! (moxie/gc edition)

Allow me to introduce you to moxie/gc.

Moxie/gc is a compile-time type-safe, highly expressive, practical functional programming language designed for **fast compilation and fast execution (FCFX)**. Its context-free grammar can be parsed and type-checked in a single pass, so compiles are fast, and the burdensome build times of other languages become somebody else's problem.

Moxie/gc compiles straight to machine code, so there's no bytecode standing between you and the hardware. And because the moxie/gc-to-hardware mapping is so tight, moxie/gc runs impossibly fast. Best of all, you never have to give a thought about memory: moxie/gc has a garbage collector (GC) built for short pauses. **[gc]**

Moxie/gc is an offshoot of moxie, its close, no-GC cousin. Their differences are described in a dedicated section below. Unless otherwise distinguished, “moxie” refers to both moxie and moxie/gc.

Naturally, moxie has all the features you've come to expect in an FP language: iterators, generators, comprehensions, lambdas, monads, pipes, laziness, generics, you name it. For data, it has the usual suspects: primitive types (numbers and String), structure types (tuple and enum), collection types (Array, MultiArray, List, Set, and Dict), resource types, and a fistful of others for good luck. Last but not least, as in any respectable FP language, functions are first-class citizens.

In short, moxie is perfect for Top Gun FP programmers who feel the need for speed.

You're welcome!

## Get it running

You can try moxie/gc three ways, from least to most effort. Remember that what you run is the reference interpreter, not a compiler, so nothing here produces a native program.

1. **In your browser.** [Try moxie/gc](try.html) runs a program (and the [REPL](repl.html) is an interactive session) on this site, with nothing to install (tick "moxie/gc rules" for this dialect). It's a sandbox: no network, no native libraries, and files that live only in the page.
2. **Download the interpreter.** [moxie.zip](../moxie.zip) is the whole interpreter, and it needs only Python 3.11 or later. Unzip it, save the lines below as `hello.mxi` next to the `moxie` folder, and run it from there:

   ```
   class_name = "Moxie 101"
   println("Welcome to $class_name")
   ```

   ```
   $ python3 -m moxie --gc run hello.mxi
   Welcome to Moxie 101
   ```

   `python3 -m moxie --gc check hello.mxi` checks a program without running it, and `test` runs its `test` blocks. `python3 -m moxie --gc repl` opens an interactive session: type an expression and see its value and type, and refer to earlier results as `res1`, `res2`, or `it`.
3. **Clone the repository.** `git clone https://github.com/slconverse1/moxie` also gets you the examples and the interpreter's own tests, and `python3 -m moxie run examples/gradebook.mxi` runs a sample.

**On a Mac.** Check `python3 --version` in Terminal. If it is older than 3.11, install a current Python from python.org or with `brew install python`. Then:

```
mkdir -p ~/moxie-work && cd ~/moxie-work
curl -LO https://slconverse1.github.io/moxie/moxie.zip
unzip moxie.zip
python3 -m moxie --gc run hello.mxi
```

with `hello.mxi` saved next to the `moxie` folder. To run moxie from any folder, add `export PYTHONPATH="$HOME/moxie-work:$PYTHONPATH"` and `alias moxie='python3 -m moxie --gc'` to `~/.zshrc`, run `source ~/.zshrc`, and then `moxie run main.mxi` works anywhere, with the gc rules. The interpreter reaches native libraries through `ctypes`, which the browser version cannot do.

The [Tutorial](tutorial.html) builds one program step by step and assumes you have it running.

## About us

Regrettably, moxie doesn't have a real compiler yet. Sorry, guys! What it does have is a complete specification and a working reference interpreter, so it no longer exists on paper alone. It's a software project undertaken by me, Steve Converse (feature selection), in collaboration with Google's generative AI (feature analysis) and Anthropic's Claude (feature selection, analysis, and implementation), without whom the rapid evolution and rigorous validation of the language wouldn't have been possible.

The interpreter runs both moxie and moxie/gc programs, including the examples in their Mixer's Guides, and it catches many mistakes before a program runs, such as mismatched types, non-exhaustive `when`s, and use-after-move. It's not the compiler, though. The things only a compiler can prove, like the speed in FCFX and the garbage collector's short pauses, are still promises, not demonstrations. **[gc]**

Of course, we're not true language designers. We're no Simon Peyton Jones, no Yukihiro Matsumoto, no Martin Odersky, no Guido van Rossum, not even close. But even so, moxie is still worth a look; its particular combination of features is truly all its own.

In the following, we show why moxie is a language FPers will love. After some introductory sections, we describe its “superpowers.” Alongside this page you'll find moxie/gc’s [Spec](spec.html), [Mixer's Guide](guide.html), and reference interpreter.

## A moxie appetizer

```
tuple TrafficLight:
  status: String

fn handle_light(light: TrafficLight) Unit:
  when light.status:
    "red" ->    println("Stop")
    "yellow" -> println("Caution")
    "green" ->  println("Go")
    else: println("Unknown state")

colors = Array("red", "yellow", "green")
for color in colors:
  light = TrafficLight(color)
  handle_light(light)
```

Output: `Stop`, `Caution`, `Go`.

Assume this code lives in its own file. Notice the two-space moxie indentation. The colon after `when light.status` opens a "code block," an independent sequence of code. Here, the block is a sequence of patterns, each with a code block of its own (a single line, in this case).

## Our debts

The elegance of moxie rests on an enormous architectural debt owed to the pioneering languages that came before it, whose innovations we have shamelessly "borrowed." Here's the list, as best we can reconstruct it:

- **Go:** interfaces, goroutines, channels, and `select`, and (in moxie/gc) the goal of garbage collection with short pauses **[gc]**, and `moxie fmt`, a formatter with no layout options, in the spirit of `gofmt` (it fixes indentation, blank lines, and operator spacing; it does not rewrap long lines).
- **Python:** clean, human-readable visual spacing (indentation opens blocks), `and`/`or`/`not`, `x in s`, slicing with ranges, and doctests, examples in doc comments that run as tests.
- **Kotlin:** scoped receiver blocks, field delegates (`level: Int delegate(Percent)` is Kotlin's `by`), Domain-Specific Languages, and labeled `break` and `continue`.
- **Scala:** opaque types, contextual parameters (`using`), expression-based syntax, its first-character precedence rule for operators you define, `for`/`yield` comprehensions, enums with fields, `tailrec`, which makes a recursive call that isn't a tail call an error, and type-level programming: matching on types, recursion, and numbers and strings as types.
- **Ruby:** its block argument and trailing `if`.
- **Rust:** the `?` error-propagation operator, `Result` instead of exceptions, no null, `impl` blocks, `Self`, let-else, `todo`, and doctests and `moxie doc`, which writes documentation that includes contracts.
- **Clojure:** lock-free state through Atoms and `swap`, `cond`, and (in moxie/gc) persistent collections that share structure. **[gc]**
- **Haskell:** multi-clause function definitions, `deriving`, `@` patterns, `Functor`/`Applicative`/`Monad` and their operators, typeclass-style interfaces with associated types, infix functions in backticks, guards on function clauses, list helpers such as `zip_with`, `span`, `split_at`, `intersperse`, and `reduce_right`, and QuickCheck-style property tests (`forall`).
- **F#:** the `|>` pipeline, its startup execution model, and its computation expressions.
- **Standard ML and OCaml:** the unification of tuples and parameter lists.
- **Node.js:** module-level code (code that runs when the module loads).
- **Swift:** named tuples, keypaths that act as lenses, and properties: computed, lazy, and static, with `will_set` and `did_set` observers (Swift's `willSet` and `didSet`).
- **Elixir:** the pin (`^`) operator for pattern matching.
- **Eiffel:** contracts, with `requires` and `ensures` on functions and interface members and `invariant` on tuples, checked in debug builds.

By synthesizing these features and others into an elegant mash-up, moxie balances its expressiveness against FCFX constraints.

## Moxie’s two dialects

As acknowledged, there are two dialects of moxie: the no-GC, moxie dialect, and moxie/gc, the GC dialect. The two are kept apart because they make different promises, so every passage of this moxie/gc edition related to garbage collection is marked **[gc]**, as shown above. Unmarked text is fundamentally the same in both dialects. See also the [moxie/gc Spec](spec.html), the [moxie/gc Mixer's Guide](guide.html), the [moxie/gc Tutorial](tutorial.html), and the [no-GC moxie page](../).

Patterns, pipes, generics, interfaces, results, fibers, and channels are the same in both dialects. Only the memory model changes in moxie/gc, and with it a good deal of what moxie can't do. Here’s what's different, at a glance: Programs aren't meant to move between the two unchanged: anything written for moxie that leans on `String[n]`, `static` strings, `copy`, fixed capacities, or pools will need edits. The full set of differences—the ways in which moxie/gc strips away the limitations of no-GC moxie—is as follows:

- **Memory.** One shared heap, reclaimed by a generational collector that works in short slices. There is no startup tally, no S-space or T-space, and no pools.
- **Sizes.** `List`, `Dict`, and `Set` grow as needed. A declared size is only a hint. `Array` and `MultiArray` still carry their sizes in their types.
- **Updates.** `List`, `Dict`, and `Set` are persistent, so an update shares structure with the old version.
- **Strings.** One `String` type. There is no `String[n]`, no `static`, and no "lasts until the next reset."
- **Closures.** A function type is just its signature, so a closure can go in a Dict, a tuple field, or a channel, and a function can return a different closure from each branch.
- **Streams.** A stream can be returned from a function, unless it borrows a resource.
- **Resources.** Atoms, channels, timers, and futures can be created anywhere, loops included. Ownership and moves work as before.
- **Fibers.** Created on demand, with no slots reserved in advance. A cap is optional.
- **Pauses.** Short, not zero. A full heap ends the program, and memory can leak through a structure that keeps growing.

## Immutability, and the fine print

Moxie's values are immutable, and the guarantee is simple: **once a value exists, it never changes.** No operation, anywhere, alters a tuple, list, string, or any other value in place. "Updating" something means building a new value and rebinding a name to it. That's why `p.score += 10` is shorthand for rebuilding `p`, why a `List` grows with `list += 4`, and why old versions of your data stay valid for as long as you hold them.

The fine print:

- **Names can be rebound.** `x += 1` doesn't change a value; it points `x` at a different one. Loops work the same way, carrying their bindings forward from one iteration to the next.
- **Updates share structure.** **[gc]** `List`, `Dict`, and `Set` are persistent: an update builds a new version that shares most of its storage with the old one, so `list += 4` is cheap, and holding on to old versions costs very little. (`Array` and `MultiArray` are flat blocks, and updating one copies it, so use a `List` for element-by-element changes.) `moxie build --report` shows where your program allocates the most.
- **Atoms are the only kind of mutable state.** An Atom is a managed cell that holds an immutable value and swaps in a new one, lock-free, through a pure function (`swap(counter, _ + 1)`). Readers always get an immutable snapshot.
- **`ref` parameters look like mutation but aren't.** The callee gets a copy, rebinds it, and the final value is copied back out to the caller's variable. Nobody ever holds two names for one changing thing.
- **Resources are stateful.** A channel end, a timer, or a database connection is a handle with an identity, so it's *moved* (one owner at a time) rather than copied. A tuple that holds a resource is a resource too.

## The Moxie Runtime

The Moxie Runtime is the small piece of machinery that starts your program, schedules its work, and cleans up after it. Before the details, two terms you'll see throughout:

**Fibers.** A fiber is moxie's unit of concurrent work: a function running with its own call stack. The entry file is the first fiber, and a program can start more. Fibers are cheap, because each one starts with just a small stack, and they share nothing except Atoms and channels. **[gc]** (They do share one heap, which is safe because values never change.) Fibers talk to each other by passing values over channels.

**`run`.** The keyword `run` starts a function as a new fiber. It returns right away, without waiting for the new fiber to do anything, and the new fiber joins the Runtime's ready queue. `run` hands back a `Result`. **[gc]** It can fail only when you've capped a fiber function with `fiber[3] fn` and all of its slots are in use.

**Fibers and OS threads.** Fibers are what other languages call green threads: the Runtime schedules them itself instead of asking the operating system to. All fibers run on a single OS thread, taking turns. A fiber runs until it parks (waits) at a `read`, `write`, `sleep`, `select`, or database query, and then the Runtime picks the next ready fiber. Nothing preempts a running fiber, so two fibers never run at the same instant. That's why they can share Atoms without locks, and also why a fiber stuck in a long computation holds up the rest. (Multi-core scheduling is an open question.)

**What other languages call them.** If you know one of these, you already know the idea:
- **Go:** a goroutine, and `run f()` is moxie's `go f()`. Go spreads goroutines across many OS threads and can preempt them, while moxie doesn't.
- **Kotlin:** a coroutine, started with `launch`.
- **Erlang and Elixir:** a process, started with `spawn`. Processes also talk by messages, but they're preemptively scheduled and each has its own heap, while moxie/gc fibers share one program heap. **[gc]**
- **Python:** an `asyncio` task, which is also cooperative and single-threaded.
- **Haskell:** a green thread, started with `forkIO`.
- **Java (21 and later):** a virtual thread.

Beyond that, the Runtime is small, and it hates surprises:

- **Memory is one shared heap, collected for you.** **[gc]** All fibers allocate from the same heap, and a generational collector reclaims what nothing can reach. New values are collected often and cheaply, and values that survive move to an older generation that is collected less often. The collector works in short slices at moments when a fiber parks or allocates, so pauses stay short. They aren't zero, and the claim is still a promise until there is a real collector. There is no startup tally, no pool to size, and no S-space or T-space. A name you are finished with doesn't keep its value alive, because the collector counts a local only until its last use, so holding the head of a long list by accident isn't a problem.
- **Resources are released at known points, not by the collector.** **[gc]** A channel end, a write handle, or a connection is a one-owner handle, and it is closed when its owner lets go of it, never whenever the collector gets around to it. That is why a dropped write end can reject its future with `ABANDONED` right away. There are no finalizers.
- **A full heap ends the program.** **[gc]** The Manifest sets a limit on the heap. When any fiber needs memory after a full collection and the limit is reached, the Runtime prints a diagnostic and ends the whole program, because a heap that all fibers share is a heap that's full for all of them.
- **Memory can leak again.** **[gc]** No-GC moxie runs in constant memory forever. With a garbage collector, a loop that keeps adding to a list, an Atom that keeps every message, and a Dict that is never trimmed all grow without end, because the collector frees only what nothing can reach. (A variable you're done with doesn't count. This is about structures the program itself keeps.) A `Ring` is the standard way to keep only recent history.
- **An abort ends the program.** If a fiber hits an unrecoverable fault (an out-of-range index, an overflow, a division by zero, `todo`, a failed assertion), the Runtime prints a diagnostic with file, line, and function, drops the fiber's resources, and ends the program with a non-zero exit, whichever fiber it was. A fault means a bug, so there's little reason to carry on.
- **Everything is linked statically from source,** Go style, with unreachable code pruned and a link report of what each package contributed. No code is loaded at run time.

## Function declarations and signatures

You'll see a lot of function declarations from here on, so here's how to read one. The shape is:

```
fn name[generics](parameters) ReturnType:
  body
```

The name comes first, then optional generic parameters in square brackets, then the parameters in parentheses, then the return type, then a colon that opens the body. The last line of the body is the value, so you rarely need `return`. It exists for programmers coming from other languages, though, and is handy for an early exit: `return value` leaves the function at once, as in a guard clause. A `return` on a function's last line is redundant, so the compiler warns about it. Here are some example declarations:

```
fn add(x: Int, y: Int) Int:
  x + y

fn greet(name: String, greeting: String = "Hello") String:
  "$greeting, $name!"

fn announce(msg: String) Unit:
  println(msg)

fn largest[T: Ordered](a: T, b: T) T:
  if a < b: b else: a

fn apply_twice(f: (Int) -> Int, x: Int) Int:
  f(f(x))

fn make_adder(n: Int) (Int) -> Int:
  (x): x + n
```

- **Parameters** are written `name: Type`, with the same colon a tuple field uses, and they're separated by commas with none after the last. A default (`greeting: String = "Hello"`) must come after the parameters without one.
- **Calls** can use position, names, or both: `greet("Ada")`, `greet("Ada", greeting: "Hi")`.
- **The return type is required.** A function that returns nothing says `Unit`, as `announce` does.
- **Generics** go in the brackets after the function name. `[T: Ordered]` says "any type `T` that has an ordering," which is what lets `largest` use `<`. The bound after the colon names an interface (`Ordered` in this case), and size parameters such as `N` live in the same brackets.
- **Modifiers** go in front of a parameter (`ref n: Int`, `lazy x: Int`, `using who: String`) or in front of `fn` (`pure fn`, `inline fn`, `fiber fn`, `export fn`).
- **Short bodies** can sit on the same line as the colon: `fn double(x: Int) Int: x * 2`.
- **Multi-clause function definitions** make one function that matches on its arguments.

**Signatures.** Every declaration has a signature, which is the function's type. Take away the name, the parameter names, and the body, and what's left is the signature, written with an arrow: the parameter types in parentheses, then `->`, then the result type. The arrow appears only in signatures, never in a declaration's own return type. Here are four declarations and their signatures:

```
add           (Int, Int) -> Int
announce      (String) -> Unit
apply_twice   ((Int) -> Int, Int) -> Int
make_adder    (Int) -> (Int) -> Int
```

Signatures matter because they are the type of a parameter that is itself a function. `apply_twice` is a declaration that takes a function. Its parameter `f` has the signature `(Int) -> Int`, which says "any function that takes an `Int` and returns an `Int`":

```
fn apply_twice(f: (Int) -> Int, x: Int) Int:
  f(f(x))

fn run_it(g: ((Int) -> Int, Int) -> Int) Int:
  g((n): n + 3, 10)

println("${apply_twice((n): n * 2, 5)} ${run_it(apply_twice)}")
```

Output: `20 16`. In the first call, `f` is `(n): n * 2`, so `5` becomes `10` and then `20`. `run_it` takes a parameter `g` whose signature, `((Int) -> Int, Int) -> Int`, is exactly `apply_twice`'s own signature, so `run_it(apply_twice)` is legal: `g` adds `3` to `10` twice, giving `16`.

**Anonymous functions.** `(n): n * 2` is a function with no name, and the missing name is what makes it anonymous. Other languages call this a lambda, and in these pages the two words mean the same thing. Size has nothing to do with it: an anonymous function can be one expression or an indented block of many lines, it can have typed parameters and a return type, and it is a value like any other, so it can be passed, returned, or bound to a name. A function written without `fn` is a lambda and is pure; write `fn (x): ...` for an anonymous function that may print, park, or touch a file, a socket, a channel, or SQL. Two shorter forms cover the common cases: a placeholder (`_ * 2`, section 9) and a function written after a call (`map()(x): x * 3`).

**A function that returns a function.** A function can give back another function as its result, and its signature shows it. The arrow reads right to left, so `(Int) -> (Int) -> Int` is "takes an `Int` and returns a function that takes an `Int` and returns an `Int`." The signature describes such a function: you give it one `Int`, and what you get back is not a final answer but a function still waiting for a second `Int`. Only when you supply that one do you get the final `Int`. `make_adder`, declared above, is such a function, and `add_curried` is another:

```
fn add_curried(a: Int) (Int) -> Int:
  (b): a + b

fn apply_curried(f: (Int) -> (Int) -> Int, a: Int, b: Int) Int:
  f(a)(b)

add5 = make_adder(5)
println("${add5(10)} ${apply_curried(add_curried, 3, 4)}")
```

Output: `15 7`. Read `make_adder(n: Int) (Int) -> Int` in three pieces: the name and parameter `make_adder(n: Int)`, then the return type `(Int) -> Int` (a function from `Int` to `Int`), then the body, whose last line is the function being returned. In `apply_curried`, the parameter `f` has the two-step type, so `f(a)` is itself a function and `f(a)(b)` calls it. `add_curried` fits `f`'s type exactly: it is classic currying, written out by hand, which is what the prelude's `curry` does for you.

## Call by value, name, need, and reference

A function has four ways to receive an argument, and moxie supports most of them:

- **By value** is the default. The argument is evaluated once, before the call, and the function gets its own value. Nothing it does can change your variable.
- **By name** is for a parameter marked `lazy`. The argument isn't evaluated before the call. It's evaluated each time the function reads the parameter, and never if the function never reads it. That makes `lazy` the right tool for a fallback value or an expensive default that's needed only sometimes. A lazy argument can't contain a `ref`.
- **By need** is by name with a cache, so the argument is evaluated at most once. Moxie doesn't build this in, since nothing is cached for you. If you want it, read the lazy parameter once, bind the result to a name, and use that name.
- **By reference** is for a parameter marked `ref`. Despite the name, it isn't a shared pointer. The function gets a copy, may rebind it, and when the function returns, the final value is copied back into the caller's variable. Both sides say so: the parameter is declared with `ref`, and the caller writes `ref` in front of the variable, so a change to your variable is always visible at the call. A `ref` parameter the function never changes draws a compiler warning, and `ref` can't be combined with `lazy`.

## Avoiding the pyramid of doom

Anyone who has written code where every step can fail knows the pyramid of doom. You check the first result, and if it's good you indent and check the second, and if that's good you indent again, until the real work sits at the far right of the screen under a stack of closing brackets. Every level has its own "what if this failed?" branch, and the branches all say the same thing.

Here's that shape in moxie, with three lookups that each return a `Result`:

```
fn pay_nested(id: Int) Result[Int, Error]:
  when find_user(id):
    Err(e) -> Err(e)
    Ok(user) ->
      when find_rate(user):
        Err(e) -> Err(e)
        Ok(rate) ->
          when find_hours(user):
            Err(e) -> Err(e)
            Ok(hours) -> Ok(rate * hours)
```

It works, but it's the pyramid. Moxie gives you several ways to flatten it, and they all keep the compiler's checking:

- **`?` hands the failure back for you.** A `?` after a call means "if this failed, return the error to my caller; otherwise give me the value." The same function becomes four flat lines, and every error still reaches the caller:

  ```
  fn pay_flat(id: Int) Result[Int, Error]:
    user = find_user(id)?
    rate = find_rate(user)?
    hours = find_hours(user)?
    Ok(rate * hours)
  ```

- **Let-else is a guard clause for a pattern.** When the value has to have a particular shape, `Active(_, rank) = acct else: fail(7, "account closed")` binds the pieces and bails out on the spot if the shape is wrong, so the rest of the function stays at the left margin (see the section on expressions above).
- **A `for:` comprehension chains steps that depend on each other.** Each line can use the names bound above it, and the first failure ends the chain:

  ```
  fn pay_for(id: Int) Result[Int, Error]:
    for:
      user in find_user(id)
      and rate in find_rate(user)
      and hours in find_hours(user)
      yield rate * hours
  ```

- **`|>>` does the same with a pipeline** when each step needs only the result of the one before it, and an early `return` or a trailing `if` (`return fail(1, "negative") if n < 0`) handles the simple guards.

All three versions give `Ok(400)` for a good id, and for a bad id they all give the same `Err` from the failing lookup. The checking didn't go anywhere. You just don't have to write it out at every level.

## Err vs Error

These two names look alike but do different jobs, and you'll meet both in nearly every moxie program.

**`Err` is a case of `Result`.** A `Result[T, E]` is either `Ok(value)`, holding the answer, or `Err(error)`, holding the reason it failed. `Err` is the "it didn't work" wrapper, and it can hold *any* error type `E` you choose.

**`Error` is a built-in tuple** that is the standard moxie error type, `Error(code: Int, message: String)`, where the message is an ordinary `String`. **[gc]** (In no-GC moxie it has to be a fixed string known at compile time.) The function `fail(code, message)` is shorthand for building an `Err` that holds one:

```
fn check_age(age: Int) Result[Int, Error]:
  if age < 0: fail(1, "negative age") else: Ok(age)

when check_age(-5):
  Ok(a) -> println("age $a")
  Err(e) -> println("error ${e.code}: ${e.message}")
```

Output: `error 1: negative age`. So `fail(1, "negative age")` is the same as `Err(Error(code: 1, message: "negative age"))`: `Err` is the `Result` wrapper and `Error` is what's inside it. Moxie also reserves a few `Error` codes for its own failures, such as `CLOSED`, `MISSING`, `OUT_OF_RANGE`, and `NO_SLOT` (what `run` returns when a fiber function's declared cap is full) **[gc]**.

When the caller needs to know *what* went wrong, use your own enum as the error type instead of `Error`. The `Err` wrapper is the same either way:

```
enum AgeError:
  Negative,
  TooOld(limit: Int)

fn check_age2(age: Int) Result[Int, AgeError]:
  if age < 0:
    Err(AgeError.Negative)
  else:
    if age > 99: Err(AgeError.TooOld(99)) else: Ok(age)

when check_age2(120):
  Ok(a) -> println("age $a")
  Err(AgeError.TooOld(limit)) -> println("over $limit")
  Err(AgeError.Negative) -> println("negative")
```

Output: `over 99`. Because the error is an enum, the compiler checks that your `when` covers every case. The `?` operator works with either kind: it passes an `Err` up to your caller, and it can convert one error type into another when you've written a `From` impl that says how.

# Moxie's Superpowers

What follows is a list of moxie's "superpowers" which, as I see it, run roughly from least to greatest. So here goes:

## 1. Legacy code

Of which there's none, so backward compatibility isn't an issue. Made from scratch, moxie has no legacy mixers to please. The moxie design arose *ex nihilo*, not from ashes, but from pure driven snow.

## 2. Top-level files everywhere

Any moxie file can hold executable statements at its top level. There's no `main` to write and no wrapper to put around your code, so the appetizer above is a complete program as it stands.

The Manifest is a small `Moxie.toml` file that sits beside your source files. Here is one for a program made of two files:

```
name = "app"
files = ["util.mxi", "main.mxi"]
entry = "main.mxi"
```

`name` names a package, `files` lists its source files in load order, and `entry` declares which file is the program's entry point. The Moxie Runtime starts the program at that file's first executable statement. Other files in the package run their own top-level code as they load, and the entry file's body runs after that. Unlike Haskell, there's no IO monad running the show.

The entry package's Manifest also sets limits that the Runtime checks at startup, such as an optional default cap on how many instances each fiber function can have alive at once, and the size of the heap: **[gc]**

```
[fibers]
limit = 8

[memory]
heap = "256MiB"
```

The manifest is also where a program's permissions live (superpower 20): a `[permissions]` table lists what it may read, write, connect to, and load.

The values here are only examples. The `limit` is a default for each fiber function, not a total for the program. A fiber function that declares its own limit (`fiber[3] fn`) uses that number instead, which means at most three copies of it alive at a time. With a `limit` of 8, one unannotated fiber function and one `fiber[3]` function, a program can have at most 1 + 8 + 3 = 12 fibers (the entry fiber plus the sum of the limits). The limit says how many copies of a function can be alive, not how many fibers that function starts. A size like `"64KiB"` is 1024-based while `"64KB"` is 1000-based. The Manifest also names the database schema that SQL is checked against, but that's a story for another day.

## 3. Everything is an expression

The core benefit of an "everything is an expression" language is that code is built from expressions, and every expression returns a value.

In an imperative language, code is split into two worlds: statements (which perform an action or change state but return nothing, like `if`, `for`, or variable assignments) and expressions (which compute a value, like `5 + 3`). Expression-based languages eliminate statements entirely. In moxie the only things that aren't expressions are declarations such as `fn`, `tuple`, and `enum`.

**Superior composability**

Because every construct in an expression-based language produces a value, you can nest any piece of code inside any other piece of code. You don't have to worry about whether a language feature is "allowed" inside an assignment.

- **In an imperative language:** You can’t assign an `if` statement directly to a variable. You have to declare a mutable variable first, then alter it inside a block.
- **In an expression-based language:** You can plug an `if`, a `match`, or a `do` block anywhere a value is expected.

```
// The 'when' block evaluates to a string,
// which is immediately assigned.
user_role = when user.clearance:
  1 -> "Admin"
  2 -> "Manager"
  else: "Guest"
```

**Elimination of temporary mutable state**

When `if` blocks or `switch` statements in an imperative language don't return values, you’re forced to create "garbage" variables to hold temporary data while your code figures out what its value should be.

Look at the difference when calculating a discount.

Statement-based:

```
let discount;       // 1. Declare an empty mutable variable
if (isMember) {
  discount = 0.2;   // 2. Mutate it here
} else {
  discount = 0.0;   // 3. Mutate it there
}
```

Expression-based:

```
// No mutation, no temporaries. The block evaluates to the value.
discount = if is_member: 0.2 else: 0.0
```

By making everything an expression, you drastically reduce the surface area for bugs caused by variables being accidentally modified or read before they’re initialized.

**Referential transparency**

In FP, a core goal is referential transparency—the idea that you can replace a function call with its resulting value without changing the program's behavior.

In a statement-based language, moving code around is dangerous because statements often rely on when and where they change the surrounding environment (side effects). In an expression-based language, code behaves cleanly like mathematics: `f(x)` simply yields a result, making it incredibly easy to reason about, refactor, and test. Moxie doesn't promise purity everywhere, though: a function can still print, read a channel, or swap an atom, and the compiler works out which functions do. Mark a function `pure fn` and the compiler enforces it.

**Specifically:** bindings, `if`, `when`, `select`, `do:` blocks, and loops all have a value in moxie, and the last line of a block *is* its value:

```
label = if area > 50:
  "big"
else:
  "small"
```

A loop can have a value, too. `break(x)` leaves with one, and `else:` supplies one when the loop runs dry. Labels like `#outer` let you break out of nested loops, and a labeled `do:` gives you an early exit with a value. A `return` in the middle of a function is the usual guard clause, and a let-else is a guard clause in one line.

**What's a let-else?** It's a binding that's allowed to fail, with the "what then?" written right next to it. On the left you write the pattern you expect the value to have, and after `else:` you say what to do if it doesn't:

```
enum Account:
  Active(name: String, rank: Int),
  Closed

fn rank_of(acct: Account) Result[Int, Error]:
  Active(_, rank) = acct else: fail(7, "account closed")
  Ok(rank * 10)
```

If `acct` is `Active`, then `rank` is bound and the function carries on to the next line, so `rank_of(Account.Active("ada", 3))` is `Ok(30)`. If it's `Closed`, the function stops right there and returns the `else:` value, so `rank_of(Account.Closed)` is an `Err`. The pattern can be anything `when` accepts, and the names it binds are in scope for the rest of the block. (Without let-else, you'd write a `when` with one useful arm and one bail-out arm, and indent everything after it.) In the entry file, the `else:` value ends the program (an `Err` prints its diagnostic and exits with a non-zero status). In addition, if a let-else pattern can never fail, as in `(a, b) = pair` where `pair` is always a two-part tuple, the `else:` could never run, so the compiler warns you that it's pointless.

## 4. No null

Every programmer is well aware of the hazards of null. Well, moxie bans null altogether.

So moxie has no null (and, obviously, no nullable types) and no "zero value" standing in for a missing one. Every binding needs a value. When something might legitimately be absent, you say so in the type: a `Result`, a `T | ()` union, or an enum of your own. Then the compiler makes you handle it, and a forgotten case is a compile error instead of a 3 a.m. crash. (`()` is the only value of the type `Unit`, and `Unit` is the empty tuple type, so `Int | ()` means "an `Int`, or nothing.")

"But now I have to check Results all day!" Not so. Moxie works hard to keep that to a minimum:

- A `?` after a call says "if this failed, hand the error back to my caller," so one character replaces a whole `if`. (The section, "There is no try," has the full story.)
- `.get_or(0)` supplies a default on the spot.
- A `Result` of a tuple forwards field access, so `find_user(id).name` is itself a `Result`, and the error goes along for the ride.
- Let-else turns "unwrap or bail out" into a single line.
- Bounded types (`Int[0..=100]`) and exhaustive `when` checking move whole classes of "what if it's missing or wrong?" out of run time and into the compiler.
- Truly impossible situations (an out-of-range array index, say) abort the fiber with a diagnostic instead of making you thread a Result through code that can't recover anyway.

## 5. Numbers that tell the truth

Integer overflow aborts instead of silently wrapping, unless you ask for `wrapping_add`, `saturating_add`, or `checked_add` by name. A range can live in the type (`Int[0..=100]`), and a `when` that covers the range needs no `_` arm. Big integers have a fixed size (`BigInt[128]`) and are stored inline. **[gc]** `Decimal[10, 2]` does exact money math, and rounding is always something you say out loud (`round_to[2](x, #half_even)`). Floats follow IEEE and warn you when you compare them with `==`.

## 6. Data paths: lenses you get for free

A path like `/User/firm/name` names a spot inside nested tuples, and it's an ordinary function, so you can store it, pass it, and compose it:

```
b = replace(a, /User/firm/name, "Acme")
c = modify(a, /User/firm/name, (s): "$s Ltd")
```

You never write the nested-copy boilerplate, and the original `a` is untouched.

## 7. Tuple and parameter-list unification

This comes straight out of the SML/OCaml playbook: **a tuple and a parameter list are the same idea.** In most languages those live in separate silos, with different syntax, different compiler rules, and boilerplate to convert from one to the other. In moxie, a function's parameter list is a compile-time named tuple. Parameters use the same colon as tuple fields (`fn greet(name: String, age: Int)`), and the two follow the same rules, so a call stops being a unique, magical event and becomes a structural assignment.

**How this differs from the classic view.** In Standard ML and OCaml the unification is literal: every function takes exactly one argument, `add(3, 5)` is `add` applied to the tuple `(3, 5)`, and tuples are positional only. Moxie unifies the *rules* rather than the representation. A function still has several parameters, and a tuple can fill the whole list, but a parameter list also gets everything a tuple field gets: names, defaults, spreads, and calls by position, by name, or both. Parameter modifiers such as `ref`, `lazy`, and `using` have no tuple counterpart, so the unification stops there. The unification reaches the type system, too: a function type is just its parameter types, so `(Int, Int) -> Int` and `((Int, Int)) -> Int` are one type, and a function of that type can be called as `f(3, 5)` or `f(pair)`. The modifiers are the exception. A tuple can't fill a `ref` parameter, and a function with modifiers has a type of its own. So a moxie programmer gets more than the ML one does, and the ML programmer's single-argument mental model still holds for everything that isn't a modifier.

**Tuples replace structs.** Moxie has no `struct` or `class`. A declared `tuple` is the record type: named fields, defaults, derived `show`, `eq`, `ord`, `read`, and `hash` (print, compare for equality, order, parse back from text, and use as a Dict key), delegates, and `impl` blocks for methods. Because a tuple follows the same rules as a parameter list, it plugs straight into the rest of the language. A tuple can fill a function's parameters, so it flows through `|>` pipes from stage to stage with no unpacking. It can be spread (`Point(...p, y: 9.0)`), matched by position or by name in a `when`, and handed along a monad sequence: if `lookup` returns a `Result[(Int, Int), Error]` and `total` takes `(a: Int, b: Int)`, then `lookup(id) |>> total` passes the pair inside the `Ok` into `total`, and `|>>` works the same way on any type with a `Monad` impl. A traditional struct is a closed bag of fields with rules of its own. It can't fill a parameter list, so every stage of a pipe or a monad chain would have to take the struct whole and pick it apart by hand, or you'd write adapter code between stages. You can still get the job done that way, but the operators lose most of their expressiveness. That’s why moxie doesn't offer a second way to make records.

To make that concrete, take `fn add(x: Int, y: Int) Int` and `pair = (3, 5)`. In SML there are two ways to call it, and both are positional: `add (3, 5)` and `add pair`. In moxie, all of these work:

```
add(3, 5)          // by position
add(x: 3, y: 5)    // by name
add(y: 5, x: 3)    // by name, in any order
add(3, y: 5)       // by position, then by name
add(pair)          // a tuple fills the whole parameter list
add(...pair)       // or spread it
```

```
fn sum_squares(x: Double, y: Double) Double:
  x * x + y * y
pt = (x: 3.0, y: 4.0)
println("${sum_squares(pt)} ${sum_squares(...pt)}")
```

Output: `25.0 25.0`.

Here's some of what unification buys you:

- **One idea to learn, not two.** Building a tuple, calling a function, and rebuilding a value with one field changed (`Point(...p, y: 9.0)`) all follow the same rules, so there are no "parallel but slightly different" syntaxes to memorize. What you know about one carries over to the other.
- **Argument bundling.** A tuple is "the setup for a call" as a first-class value. Build it once, store it, pass it around, and feed it to a function with no unpacking and no adapter code. Returning several values is just returning a tuple.
- **Calls are as flexible as you want.** Call by position, by name, or by position followed by names in any order. Trailing parameters can have defaults, exactly like a tuple's trailing fields.
- **Pattern matching comes along for free.** Functions can have several clauses, and the first clause whose parameters match the arguments runs. A parameter can be a pattern instead of a name, such as the literal `0`, and a lambda's parameter can be a pattern too. Here's a factorial in two clauses:

  ```
  fn factorial(0, acc: BigInt[128]) BigInt[128]: acc
  fn factorial(n, acc: BigInt[128]) BigInt[128]: factorial(n - 1, acc * n)
  println("${factorial(5, 1)}")
  ```

  The text after each colon is that clause's body. The trick is that `acc` (short for "accumulator") is the running answer, and the multiplying happens on the way *down*, in the second clause's call, not in the first clause. The first clause only fires at the very end, when the countdown hits `0`, and its job is to hand back the finished answer. Here's `factorial(3, 1)` step by step:

  ```
  factorial(3, 1)   // n is 3, not 0, so clause 2 runs: factorial(3 - 1, 1 * 3)
  factorial(2, 3)   // clause 2 again: factorial(2 - 1, 3 * 2)
  factorial(1, 6)   // clause 2 again: factorial(1 - 1, 6 * 1)
  factorial(0, 6)   // the first argument is 0, so clause 1 runs and returns acc: 6
  ```

  Each pass multiplies `acc` by the current `n` and counts `n` down by one. By the time `n` reaches `0`, `acc` is already 3 × 2 × 1 = 6, so returning it is the whole job. Start the accumulator at `1` (the "do nothing" value for multiplication), and `factorial(5, 1)` prints `120`. The `BigInt[128]` type just means the product can grow far past the size of an ordinary `Int`.
- **Uniform higher-order code.** A stream of tuples feeds a lambda with two or more parameters (`zip(xs, ys) |> map()(x, y): x * y`), so no special adapters are needed.
- **Compiler economy.** The compiler checks escapes and carries state forward with one set of rules. For example, the bindings a `daemon:` cycle hands to its next cycle are treated as one unit, like any other tuple.
- **Pipes just work.** When a stage returns a tuple and the next stage's parameter list matches it, the value slides straight in:

```
fn fetch_sensor_data(id: Int) (Float, Float, Float):
  (12.5, 45.0, 0.8)
fn calculate_velocity(
  x: Float,
  y: Float,
  z: Float
) (speed: Float, angle: Float):
  (95.2, 14.6)
fn update_physics(speed: Float, angle: Float) Unit:
  println("Physics vector updated: speed $speed, angle $angle")
1042
  |> fetch_sensor_data()
  |> calculate_velocity()
  |> update_physics()
```

Output: `Physics vector updated: speed 95.2, angle 14.6`. There are no intermediate variables, no `result(0)` plucking, and no zip adapters.

**Splatting and gathering.** Other languages use two common terms. *Splatting* spreads one bundle out into separate slots, and *gathering* collects separate values back into one bundle. Moxie does both with the same `...`, and a tuple makes most of it automatic:

```
fn add(x: Int, y: Int) Int: x + y
fn total(base: Int, numbers: ...Int) Int:
  numbers |> to_stream() |> reduce(base, _1 + _2)
pair = (3, 5)
values = Array(10, 20, 30)
print("${add(...pair)} ${total(100, 1, 2, 3)} ${total(100, ...values)} ")
println("${total(100)}")
fn describe(xs: Array[Int][3]) String:
  when xs:
    Array(first, ...rest) -> "first $first, then ${len(rest)} more"
println(describe(values))
p = (x: 1, y: 2)
println("${(...p, y: 9)}")
```

Output: `8 106 160 100`, then `first 10, then 2 more`, then `(x: 1, y: 9)`. Here's where each one shows up:

- **Splatting:** `add(...pair)` spreads a tuple across a parameter list, and `total(100, ...values)` spreads an array into a variadic. `(...p, y: 9)` spreads a tuple's fields into a new tuple, with later fields overriding earlier ones. In many cases you don't even need the `...`, because `add(pair)` already works when the shape matches.
- **Gathering:** `numbers: ...Int` gathers any number of trailing arguments into one list **[gc]**, and zero is fine. A pattern gathers too: in `Array(first, ...rest)` the `rest` collects whatever the pattern didn't name.
- **The limits:** A variadic has a single element type (use a union or a tuple when you need a mix). **[gc]** In moxie/gc a `List` of any length can be splatted into a call, and a `rest` is an ordinary value. (No-GC moxie has to know how many values it is spreading, so it can't splat a `List` of unknown length, and its `rest` is a read-only view that can't be returned or stored.)

**The tradeoff for unification** is currying. If everything takes its arguments as a bundle, you don't get partial application for free the way Haskell does. Moxie's answer is the placeholder call (for example, `log("ERROR", _)`, covered in the Pipes section), plus `curry(f)` in the prelude, for a function with any number of parameters, when you want classic currying. `uncurry[n](g)` goes the other way, with the count in brackets and no limit; you rarely need it, because moxie's argument bundle already is a tuple and `f(a, b)` and `f(pair)` both work.

## 8. Pattern matching

A pattern describes the shape of a value. Matching a value against patterns tests that shape, takes the value apart, binds names to the pieces, and runs the code for the first pattern that fits, all in one step. Instead of nesting `if` and `else` tests, you say what the data looks like. In moxie it's `when value:`, and the arms are tried from top to bottom.

**Sum types made safe.** Enums are moxie's algebraic data types: a value is exactly one of several cases (an OR), and each case can carry fields. A `when` is how you open one up safely:

```
enum Shape:
  Circle(radius: Double),
  Rect(w: Double, h: Double),
  Dot

fn area(s: Shape) Double:
  when s:
    Circle(r) -> 3.0 * r * r
    Rect(w, h) -> w * h
    Dot -> 0.0

print("${area(Shape.Circle(2.0))} ${area(Shape.Rect(2.0, 3.0))} ")
println("${area(Shape.Dot)}")
```

Output: `12.0 6.0 0.0`. Each arm names its case and binds its fields in the same step, so there's no cast and no null check. That is also how moxie handles "absent": a missing value is just another case, such as a `Missing` case of your own enum, that you match.

**The compiler checks that you covered everything.** Every `when` must cover every case, and `else:` is the fallback. If an enum has three cases and the `when` handles two, the program won't compile (the message is approximate):

```
fn area(s: Shape) Double:
  when s:
    Circle(r) -> 3.0 * r * r
    Rect(w, h) -> w * h      // error: `when` does not cover `Dot`
```

The payoff comes later. Add a case to `Shape` six months from now, and the compiler points to every `when` that needs a new arm, so you don't have to hunt for what might break. Enums are closed on purpose for this reason. A `when` over a bounded integer such as `Int[0..=100]` whose patterns cover the whole range needs no `_` arm either.

**Deep destructuring.** Patterns nest to any depth, so one arm can check a case, look inside a tuple, and test a literal at the same time:

```
enum Response:
  Success(user: (Int, String)),
  Failure(code: Int)

fn handle(r: Response) String:
  when r:
    Response.Success((user_id, token)) -> "log in $user_id with $token"
    Response.Failure(404) -> "not found"
    Response.Failure(_) -> "generic error"

println(handle(Response.Success((7, "abc"))))
println(handle(Response.Failure(404)))
println(handle(Response.Failure(500)))
```

Output: `log in 7 with abc`, then `not found`, then `generic error`. Without patterns, getting at `user_id` would take several lines of checks and temporary variables. Here the arm hands you `user_id` and `token` directly.

**It reads like a definition.** A function can have several clauses whose parameters are patterns, so the code mirrors the mathematical definition:

```
fn fib(0) Int: 0
fn fib(1) Int: 1
fn fib(n) Int: fib(n - 1) + fib(n - 2)
println("${fib(10)}")
```

Output: `55`. That is the textbook definition, not the fast one; the caching recipe in the laziness section is the fast one. Either way there's no loop, no counters, and no variables being incremented.

**Patterns in a parameter list.** A parameter doesn't have to be a name. It can be a pattern that takes the argument apart before the body runs, so the body starts with the pieces already bound. Here `area` is written as one clause per case, and `describe` unpacks a tuple right in its parameter list:

```
enum Shape:
  Circle(radius: Double),
  Rect(w: Double, h: Double),
  Dot

fn area(Shape.Circle(r)) Double: 3.0 * r * r
fn area(Shape.Rect(w, h)) Double: w * h
fn area(Shape.Dot) Double: 0.0

tuple Player:
  name: String,
  score: Int

fn describe(Player(name, score)) String:
  "$name has $score"

print("${area(Shape.Circle(2.0))} ${area(Shape.Rect(2.0, 3.0))} ")
println("${area(Shape.Dot)}")
println(describe(Player(name: "Ann", score: 250)))
```

Output: `12.0 6.0 0.0`, then `Ann has 250`. The clauses are tried from top to bottom, the first one whose patterns fit the argument runs, and only the first clause needs to say its types. Just as with `when`, the compiler wants the group to end with a `_` clause or to cover every enum case, so leaving out the `Shape.Dot` clause is a compile error.

**Guards.** An arm can add an `if` condition. When it's false, matching falls through to the next arm, and the logic stays flat instead of drifting to the right in nested blocks:

```
tuple Player:
  name: String,
  score: Int

fn rank(p: Player) String:
  when p:
    Player(name, score) if score > 200 -> "$name: top tier"
    Player(name, score) if score > 100 -> "$name: elite"
    Player(name, _) -> "$name: standard"

println(rank(Player(name: "Ann", score: 250)))
println(rank(Player(name: "Bob", score: 150)))
println(rank(Player(name: "Cy", score: 5)))
```

Output: `Ann: top tier`, `Bob: elite`, `Cy: standard`. A guarded arm doesn't count toward coverage, so the compiler still insists on the unguarded last arm.

**Ranges and literals.** A pattern can also be a literal, a range, or a comparison like `>= 500`, so a whole family of values reads as a table:

```
fn describe(status: Int) String:
  when status:
    200 -> "Success"
    400..=499 -> "Client Error"
    >= 500 -> "Server Error"
    else: "Unknown"

println("${describe(200)} ${describe(404)} ${describe(503)} ${describe(302)}")
```

Output: `Success Client Error Server Error Unknown`. The subject is named once, on the `when` line, and each arm only says which values it takes. Use `..=` for a closed band such as `400..=499`, and `>=`, `>`, `<=` or `<` when one end is open. A comparison works on any ordered type, so `>= 90.0` is fine for a `Double`, and its operand is a literal or a pin like `^limit`. The compiler can't tell whether comparisons alone cover every value, so a `when` like this one keeps its `_ ->` arm.

**Conditions, not just shapes.** A plain `when` is a chain of Boolean tests: the first arm that is true wins, and the chain must end with an `else:` arm. It's the right tool when the tests involve different things:

```
fn advice(temp: Int, raining: Bool) String:
  when:
    raining and temp < 5 -> "Bring a coat and an umbrella"
    raining -> "Bring an umbrella"
    temp < 5 -> "Bring a coat"
    else: "Enjoy the day"

println(advice(3, true))
println(advice(10, true))
println(advice(3, false))
println(advice(20, false))
```

Output: `Bring a coat and an umbrella`, `Bring an umbrella`, `Bring a coat`, then `Enjoy the day`. The arms are tried from top to bottom, so the most specific test goes first.

**Looking inside an object.** `x.do:` runs a block with `x` as its receiver, which puts the fields of `x` in scope as bare names. (`x.do:` works like Kotlin's `run`, with the receiver's fields in scope and the last line as the value.) Combine that with a value-less `when` and the tests can be written in terms of the object's own fields:

```
tuple User:
  is_admin: Bool,
  is_manager: Bool

fn access(user: User) String:
  user.do:
    when:
      is_admin -> "Full Access"
      is_manager -> "Limited Access"
      else: "No Access"

print("${access(User(is_admin: false, is_manager: true))} ")
print("${access(User(is_admin: true, is_manager: false))} ")
println("${access(User(is_admin: false, is_manager: false))}")
```

Output: `Limited Access Full Access No Access`.

**A whole shape at once.** A pattern can describe a nested structure down to its literals, so one arm can recognize a particular value outright:

```
tuple Point:
  x: Int,
  y: Int

tuple Rectangle:
  origin: Point,
  w: Int,
  h: Int

fn message(r: Rectangle) String:
  when r:
    Rectangle(Point(0, 0), 10, 10) -> "Standard square at origin"
    else: "Unknown"

println(message(Rectangle(origin: Point(x: 0, y: 0), w: 10, h: 10)))
println(message(Rectangle(origin: Point(x: 1, y: 0), w: 10, h: 10)))
```

Output: `Standard square at origin`, then `Unknown`.

**More patterns.** A pattern can be a literal, a range (`90..=100`), a name that binds, or `_`. Beyond that:
- `p@Account(name, score)` binds the whole value to `p` as well as its fields.
- `^limit` pins an existing variable, so the arm compares against its value instead of binding a new name.
- `List(head, ...tail)` and `Array(a, b, c)` take sequences apart, and a Dict pattern matches a subset of entries.
- Alternatives are separated by commas, and they must bind the same names.
- Patterns work outside `when` too: `value is Pattern` is a `Bool` test, a let-else bails out when the pattern doesn't match, and a pattern that can't fail may sit to the left of a binding, in `for` names, and in function and lambda parameters.

Chapter 12 of the Mixer's Guide has an example of each.

In most languages, an `if` or a `switch` checks conditions or flat values. A pattern checks the shape, the case, and the values in one step, binds the pieces for you, and lets the compiler make sure no case is left out.

## 9. Pipes and placeholders

`|>` drops the value on its left into the call on its right. The compiler tries the first and last parameters, keeps whichever type-checks, and if both do, it asks you to say which with `&` instead of guessing:

```
final_score = 10
  |> add(5, &)
  |> multiply(2, &)
```

A `seq:` stage runs every step whose condition holds, in order, each seeing the result of the one before. Each line is a condition, an arrow, and a step, and it works like a row of "if this, then do that" gates that the value passes through, with no `if`, no `else`, and no temporary variables:

```
fn is_big(n: Int) Bool:
  n > 100
fn is_even(n: Int) Bool:
  n % 2 == 0
fn halve(n: Int) Int:
  n / 2
fn bump(n: Int) Int:
  n + 1
fn tidy(n: Int) Int:
  n |> seq:
    is_big -> halve()
    is_even -> bump()
    is_big -> halve()
println("${tidy(500)} ${tidy(40)} ${tidy(7)}")
```

Output: `125 41 7`. Take `tidy(500)`: 500 is big, so it halves to 250. 250 is even, so it bumps to 251. 251 is still big, so it halves to 125. `tidy(40)` skips the two `is_big` gates and takes only the bump, and `tidy(7)` passes through all three untouched. A condition is a function applied to the current value, every step returns the type it receives, and there's no default arm, since a value that matches nothing simply flows through unchanged.

A `_` where an argument goes turns a call into a function, with no currying machinery at all:

```
fn log_error = log("ERROR", _)
```

That one line makes a plain, storable function out of `log`.

## 10. Uniform function call syntax

`x.f(args)` and `f(x, args)` mean the same thing. If `x` has no field or method called `f`, moxie looks for an ordinary function `f` and hands it `x` as its first argument. (The full lookup order is field, then method, then extension, then free function.) So any function can be called with method syntax, on any type, including types you don't own.

**Pipelines read left to right.** Nested calls read inside out: `make_header(make_alert(raw))` runs `make_alert` first, but you meet it last. With UFCS the same chain reads in the order things happen, and a line that starts with `.name` continues the statement, so a long chain stacks neatly:

```
fn add_prefix(text: String, prefix: String) String:
  "$prefix$text"

fn wrap_in_tags(text: String, tag: String) String:
  "<$tag>$text</$tag>"

fn make_alert = add_prefix(_, "[ALERT] ")
fn make_header = wrap_in_tags(_, "h1")

raw = "Server connection lost."
formatted = raw
  .make_alert()
  .make_header()
println(formatted)
```

Output: `<h1>[ALERT] Server connection lost.</h1>`. Here `make_alert` and `make_header` are partial calls (`_` marks the open slot), and the value slides into that slot.

The `|>` pipeline from the previous section gives the same left-to-right flow, and it's an alternative spelling of the same chain:

```
formatted = raw
  |> make_alert()
  |> make_header()
println(formatted)
```

The output is the same. The two differ in where the value may land: the dot always puts it in the first parameter, while `|>` tries the first and last parameters and keeps whichever type-checks (and `&` picks a slot when both would). So use dots when the data comes first, and `|>` when a function takes it last or in the middle.

**Open-world extensibility.** In a strict object-oriented language, adding a method to a class means editing its source or subclassing it. In moxie, write a plain function anywhere and call it as if it were a method. Suppose `User` is declared in a package you can't change:

```
tuple User:
  name: String,
  role: String

fn to_profile_card(user: User, theme: String) String:
  "[${user.role}] ${user.name} (Theme: $theme)"

user = User(name: "Alice", role: "Developer")
card1 = to_profile_card(user, "Dark")
card2 = user.to_profile_card("Dark")
println(card2)
```

Output: `[Developer] Alice (Theme: Dark)`, and `card1` and `card2` are the same string. There are no closed classes, nothing to subclass, and nothing to patch. (Moxie also lets you write an `impl` block for a type you don't own, which is how you make it satisfy an interface. UFCS needs no `impl` at all, only a function.)

With UFCS:

**Data stays plain data.** In FP you want data to be just data, like `User`, with behavior living in functions outside it. UFCS gives you the tidy syntax of a method call while the function stays a separate, ordinary function, with no connection to the data structure beyond its first parameter.

**One surface instead of two.** You never have to ask whether something is "a method on the object" or "a free-standing utility function." `len(xs)` and `xs.len()` are the same call.

**Data-first or data-last: no need to pick a side.** Haskell prefers the data as the last parameter, because that makes currying easy. Object-oriented languages put the data first, because the subject reads like a noun before the verb. In moxie you write the function with the data first and call it either way. The dot puts the receiver in the first slot, and `|>` tries the first and last slots, so data-last functions chain with pipes. Partial application meets UFCS the same way as above: after `fn times10 = multiply(_, 10)`, the call `5.times10()` is `50`.

**The fine print.** A field of function type wins over a function of the same name: `x.name(args)` calls the field and passes no receiver, the compiler warns when a field hides a function, and `x |> name(args)` forces the function reading. Two `impl`s that give the same name different bodies are an ambiguity error that asks you to write `Speaker.speak(x)`.

## 11. DSLs, and why moxie has no macros

Let's be clear about what DSLs are and aren't. A DSL can't alter the grammar or invent new keywords, and it doesn't generate code; it only structures ordinary calls. Macros do those things, and Kotlin, which has no macros of its own, hands code generation to compiler plugins and a symbol-processing API. Moxie has neither macros nor plugins, so we had to ask how much we'd miss them. For builder-style problems (HTML, configuration, test descriptions), not much, because the DSL tools below cover them. For generating boilerplate, moxie leans on the compiler itself (`deriving`, `test` blocks, `for:` comprehensions, and SQL that's checked against your schema). And there's a plain reason moxie can't have macros: the grammar is fixed and context-free so the compiler can parse and type-check in one pass, and a macro would rewrite the grammar in the middle of the parse.

A builder is just a set of ordinary functions, and nesting is nested calls. Variadic parameters let a parent take any number of children, and nominal tuples make it type-safe:

```
page = html(
  body(
    h1("Welcome to moxie"),
    ul(
      li("fast"),
      li("small")
    )
  )
)
```

That prints `<html><body><h1>Welcome to moxie</h1><ul><li>fast</li><li>small</li></ul></body></html>`. A `ul` accepts only `Li` items, so `ul(h1("x"))` is a compile error. The rest of the toolbox is trailing blocks, receiver blocks (`x.do:` and `x.update:`), named arguments and defaults, contextual `using` parameters, user-defined operators, and infix functions in backticks (`100 `calculate_yield` 5`). You can extend types you don't own by writing your own `impl` for them.

One thing moxie doesn't have is Kotlin's lambda-with-receiver, where a block sees an implicit parent and children register themselves as they're created. In moxie, children are returned values, not side effects. Whether we need a dedicated child-collection mechanism is still an open question.

## 12. "There is no try"

Failure is a value. A function that can fail returns a `Result`, and `?` propagates it:

```
fn fetch_total(id: Int) Result[Int, Error]:
  a = fetch_first(id)?
  b = fetch_first(id + 1)?
  Ok(a + b)
```

No exceptions flying over your head, and no hidden control flow. Not bad! Your errors can be your own enums, and `?` converts between error types when you've said how (a visible `From` impl, one hop). In the entry file, a failed `?` prints the error and exits with a non-zero status, which is exactly what you wanted.

## 13. Iterators, generators, and comprehensions

**Iterators.** Any collection is a loop source: `for x in numbers:`. A Dict yields `(key, value)` tuples, a `Range` counts (with a step, and downward step: `Range(3..=1, -1)` counts 3, 2, 1), and `zip` pairs two sources. A stream (`to_stream()`) is moxie's general iterator, and `map`, `filter`, `take`, `scan`, `enumerate`, `windows`, and their friends, are its stages.

**Generators.** A generator is a function that returns an `unfold` stream. The step takes the current state and returns a value together with the next state, or an `Err` to stop:

```
tuple Fib:
  a: Int,
  b: Int
fn fibonacci() Stream[Int]:
  unfold(Fib(a: 0, b: 1))(state):
    Ok((state.a, Fib(a: state.b, b: state.a + state.b)))
for n in fibonacci() |> take(6):
  println("$n")
```

Output: `0`, `1`, `1`, `2`, `3`, `5`. The sequence is infinite, and `take(6)` is why the loop ends. Where does `state` come from? `unfold(Fib(a: 0, b: 1))(state):` is a call with a trailing function, and `state` is that function's one parameter, so `unfold` supplies its value, not you. The first time `unfold` runs the function it passes the seed, `Fib(a: 0, b: 1)`. Each time after that it passes whatever `next_state` the previous pass returned. The function returns `Ok((value, next_state))`: `value` is the next number the stream hands out, and `next_state` is what the following pass will receive. Here's the trace:

```
state = Fib(a: 0, b: 1)   // the seed:  emit 0, next state Fib(a: 1, b: 1)
state = Fib(a: 1, b: 1)   // emit 1, next state Fib(a: 1, b: 2)
state = Fib(a: 1, b: 2)   // emit 1, next state Fib(a: 2, b: 3)
state = Fib(a: 2, b: 3)   // emit 2, next state Fib(a: 3, b: 5)
```

An `Err` instead of an `Ok` ends the stream, and this one never returns an `Err`, which is why it's infinite.

**Container comprehensions.** `List`, `Set`, and `Dict` each have one, with one `if` filter allowed and no nested `for`. **[gc]** The container grows as needed, so the declared type needs no size:

```
xs = List(1, 2, 3, 4)
squares: List[Int] = List(x * x for x in xs if x > 1)
words = List("ab", "cde")
lens: Dict[String, Int] = Dict(w: len(w) for w in words)
println("${len(squares)} ${squares(0)} ${lens(cde)}")
```

Output: `3 4 Ok(3)`. The squares are 4, 9, and 16, and a Dict lookup returns a `Result` (`ab` and `cde` have lengths 2 and 3). `Set(...)` is built the same way.

**`for:` comprehensions.** The block form comes from Scala's `for`/`yield`, widened with ideas from F# computation expressions. It chains steps that can each fail or come up empty, and stops at the first one that does:

```
good = for:
  a in Box.Full(20)
  b in half(a)
  c in half(b)
  yield a + c
```

`Box` and `half` are defined by the mixer, as the functional programming section explains. Here, we use `Box.Full(25)`, but start from 10 and you get `Box.Empty`, because 5 is odd. A `for:` comprehension works for `Box`, `Result`, streams, and anything else with the right interfaces (more in the interfaces section). A line `name = expr` binds a value, and a line that can fail to match uses a let-else (`Active(_, rank) = user else: Err(NotFound(id: id))`, explained in the "Everything is an expression" section). Independent generators joined with `and` run side by side and need less from the type *(the exact `and` parse rule is an assumption)*.

## 14. Laziness

Moxie is eager by default, so laziness is something you ask for, in two places.

**Streams.** A stream is a recipe, defined as a source plus a list of stages, and nothing happens until a terminal (`collect`, `sum`, `reduce`, `count`, or a `for` loop) pulls on it. `map`, `filter`, `take`, `scan`, `enumerate`, and the other horizontal stages are all lazy: one element travels through the entire chain, and an element that `take` or `filter` rejects is never mapped over further. That's why an infinite source costs nothing:

```
total = Range(1..)
  |> filter(_ % 3 == 0)
  |> map((n): n * n)
  |> take(4)
  |> sum()
```

That's 9 + 36 + 81 + 144, or `270`, and it never builds a list. The vertical stages (`sort`, `reverse`) must see every element first, so they collect them in a temporary buffer and break the one-at-a-time flow. (`chunks` and `windows` buffer a little, too.)

**`lazy` parameters.** Mark a parameter `lazy` and the argument isn't evaluated until the function reads it, which makes call-by-name a one-word feature:

```
fn costly() Int:
  println("computing")
  7
fn maybe(use_it: Bool, lazy x: Int) Int:
  if use_it: x else: 0
println("skipped: ${maybe(false, costly())}")
```

Output: `skipped: 0`, with no "computing" line, because `x` is never read. Be aware that a `lazy` argument is re-run on every read, so `x + x` computes it twice. If you want call-by-need, bind it once with `once = x` and use `once`.

**The fine print.**
- Nothing is cached for you, and there's no hidden memoization. Caching is a recipe you write on purpose (example below).
- A stream feeding two terminals runs its recipe twice, and the compiler warns you.
- **[gc]** A stream holds its source, and the collector keeps the source alive, so a stream can be returned from a function. The exception is a stream that borrows a resource, such as a channel end or a database connection. A helper that returns one has to be an `inline fn`. (In no-GC moxie every stream over local data is a view that can't be returned.)
- A `lazy` parameter can't also be a `ref` parameter.

**A caching recipe.** The simplest one threads a `Dict` through the recursion as a `ref` parameter, so every call can see what earlier calls learned, and wraps it in a plain function that starts the table empty:

```
fn fib_memo(n: Int, ref seen: Dict[Int, Int]) Int:
  known = get_or(seen, n, -1)
  if known >= 0:
    return known
  v = if n < 2: n else: fib_memo(n - 1, ref seen) + fib_memo(n - 2, ref seen)
  seen($n) = v
  v

fn fib(n: Int) Int:
  seen = Dict[Int, Int]()
  fib_memo(n, ref seen)

println("${fib(40)}")
```

Output: `102334155`, instantly. Without the table the same recursion makes over three hundred million calls. **[gc]** (The table needs no declared size here, because a Dict grows as needed.) (`$n` in `seen($n)` means "the value of `n` as the key". A bare `n` would be the word `n`.) The other recipes are a table built bottom-up with `reduce`, and one fiber or Atom that owns a shared table and answers over channels.

## 15. Generics

Go shipped without generics in 2009 and didn't get them until version 1.18, in 2022. A language can survive without them for a while, but it pays in copy-and-paste code and `any`-typed escape hatches. Moxie has them from the start, and the interesting part is how they say what a type must be able to do.

A generic declaration lists its type parameters in square brackets, ahead of the ordinary parameters in parentheses. The compiler works the types out from the arguments, so you rarely write them at a call:

```
fn bigger[T: Ordered](a: T, b: T) T:
  if a < b: b else: a

tuple Pair[A, B]:
  first: A,
  second: B

fn swap[A, B](p: Pair[A, B]) Pair[B, A]:
  Pair(first: p.second, second: p.first)

fn first_of[T, N where N > 0](a: Array[T][N]) T:
  a(0)

println("${bigger(3, 9)} ${bigger("pear", "apple")}")
println("${swap(Pair(first: 1, second: "one"))}")
println("${first_of(Array(7, 8, 9))}")
```

Output: `9 pear`, then `Pair(first: "one", second: 1)`, then `7`. A few things are going on here:

- **Generics sit beside the tuple, not inside it.** Everything in parentheses is the tuple (or parameter list), and it follows all the unification rules. The square brackets are a separate, compile-time-only list. Type parameters aren't values, so they never exist at run time and you can't pass one around as an argument. But a declared tuple can itself be generic, as `Pair[A, B]` shows, and it keeps every tuple rule.
- **Type dependencies are spelled out.** `T: Ordered` says that `T` must be orderable, which is what makes `a < b` legal in the body. That is a *bound*. A type meets a bound only through a visible `impl`, and the body of the function may use only what the bound provides (plus what any type allows: bind it, pass it, return it, store it). A parameter with no bound is plain data, so you can't compare it or call methods on it unless you ask for that in a bound. Several requirements join with `+`, as in `[T: Ordered + Equatable]`.
- **Bounds are checked at the call.** Here's a bound with an interface of your own:

  ```
  interface Speaker:
    fn speak() String
  tuple Dog:
    name: String
  impl Speaker for Dog:
    fn speak() String:
      "${name} says woof"
  fn announce[S: Speaker](s: S) Unit:
    println(s.speak())
  announce(Dog(name: "Rex"))
  ```

  Output: `Rex says woof`. Call `announce` with a type that has no `Speaker` impl and the compiler stops at that call and says so, instead of failing somewhere deep inside the function. You don't have to declare every interface yourself. The prelude supplies the ones generic code asks for most: `Equatable`, `Ordered`, `Hashable` (what a Dict key needs), `Show` (has `show()`), `Read` (parses text), `Addable` (has `+` and a `zero`), and `Numeric` (adds `-`, `*`, `/`, and a `one`). Numbers, `Char`, and `String` already implement the ones that make sense for them, and a type of your own joins with `deriving show, eq, ord, read, hash` or an `impl`. So a function that sums anything addable is `fn total[T: Addable](...)`, with no interface of your own to write.
- **Sizes are dependencies too.** `N` in `Array[T][N]` is a size parameter: a number known at compile time. `where N > 0` is a constraint on it, so `first_of` on an empty array is a compile error at the call, not an out-of-range crash. **[gc]** In moxie/gc only `Array` and `MultiArray` carry sizes in their types (a `List` simply grows), and generics let you write code once for every size.
- **A type parameter can be a whole argument list.** A function type is just its parameter types in order, so `(A) -> R` matches `(Int, Int) -> Int` with `A` as `(Int, Int)`, and `(String) -> String` with `A` as `String`. That means one definition covers every number of arguments:

  ```
  fn add(x: Int, y: Int) Int:
    x + y
  fn shout(s: String) String:
    "${s}!"
  fn call_with[A, R](f: (A) -> R, args: A) R:
    f(args)
  fn twice[A](f: (A) -> A, args: A) A:
    f(f(args))
  println("${call_with(add, (3, 4))} ${call_with(shout, "hi")} ${twice(shout, "yo")}")
  ```

  Output: `7 hi! yo!!`. Other languages handle this with a family of types or overloads (Scala's function types come as `Function1` through `Function22`, with a catch-all for longer lists, and Scala 3 dropped the old 22-argument limit), or with a feature like C++'s variadic templates. In moxie it falls out of tuple and parameter-list unification. The limit is that a wrapper can pass an argument list along but can't add or remove an argument, because moxie has no way to take a tuple type apart.
- **Even type constructors can be parameters.** A parameter written `F[_]` stands for something like `Box` or `Result`, so `fn double_in[F[_]: Monad](m: F[Int])` works for any monad without being written twice.
- **No cost at run time.** The compiler builds one specialized copy of the function for each set of types it's actually used with. There's no boxing, no run-time type information, and no call through a table. The price is code size, and that's the trade moxie makes on purpose, in keeping with FCFX.

## 16. Interfaces and impls (a.k.a. typeclasses)

An `interface` says what a type can do, and an `impl` says that a type does it. You can implement your own interface for somebody else's type, so you can extend things you don't own. There are bounds (`[T: Ordered + Equatable]`), default method bodies, associated types, properties (a field that can run code, computed or lazy, with observers), and conditional instances. Everything is specialized per use at compile time, so there are no tables at run time.

When you want a mixed bag of types, say `any Voice`:

```
crowd: List[any Voice] = List(Dog(name: "Rex"), Robot(serial: 7))
for s in crowd:
  println(s.speak())
```

If you're a Haskell person: class is `interface`, instance is `impl`, superclass is an embedded interface, and `Functor`, `Applicative`, and `Monad` are real interfaces over type constructors.

## 17. Functional programming

You already know the toolbox. Here's how it looks in moxie.

**Values don't change, and old versions stay valid:**

```
old = List(1, 2, 3)
new = old + 4
println("${len(old)} ${len(new)}")
```

Output: `3 4`.

**Streams are lazy**, so you can map, filter, and fold at will.

**Functions compose:** `(inc ~> twice)(5)` is `12`.

**Comprehensions** with `for:` work for any type with a `Monad` impl.

**Monad sequences read left to right, with operators.** Three operators from Haskell do the work: `|>>` is bind (run the next step on the value inside, and stop at the first failure), `<$>` maps a plain function over the value inside, and `<*>` applies a function that is itself inside a container to a value inside another. Here's `|>>` on the prelude's `Result`, which needs no setup:

```
fn half(n: Int) Result[Int, Error]:
  if n % 2 == 0: Ok(n / 2) else: fail(1, "odd")

a = Ok(20) |>> half |>> half    // Ok(5)
b = Ok(10) |>> half |>> half    // an Err, because 5 is odd
```

The `?` form of the same chain, and the `for:` form, say the same thing, just differently:

```
fn quarter(n: Int) Result[Int, Error]:
  a = half(n)?
  half(a)
```

The operators work for any type with the right impls. With a `Box` a sequence, a map and an applicative combination look like this:

```
Box.Full(20) |>> half |>> half                       // Box.Full(5)
Box.Full(10) |>> half |>> half                       // Box.Empty
inc <$> Box.Full(4)                                  // Box.Full(5)
(curry(add) <$> Box.Full(2)) <*> Box.Full(3)      // Box.Full(5)
(curry(add) <$> Box.Full(2)) <*> Box.Empty      // Box.Empty
```

Here `half` returns a `Box`, and `<$>` and `<*>` get parentheses when mixed with other operators. Use `|>>` when each step needs the previous result, and `<$>` with `<*>` when the inputs are independent and you just want them combined, with the first failure winning.

**These types aren't part of moxie.** `Maybe`, `Option`, `Either`, `Validation`, `State`, a parser type, and so on, are not built into the language or its library. What the prelude gives you is the `Functor`, `Applicative`, and `Monad` interfaces, plus ready-made instances for `Result`, `Stream`, `List`, and `Array`. For any other type, the mixer defines the type and writes its `impl Monad[...]`, and then `|>>`, `<$>`, `<*>`, and `for:` work on it. Chapter 24 of the Mixer's Guide has the full `Box` definition and its impl, with working examples.

**You can write code once for every monad:**

```
fn double_in[F[_]: Monad](m: F[Int]) F[Int]:
  m.flat_map((x): F.pure(x * 2))
```

That works for `Box.Full(21)` and `Ok(21)` alike.

**The limitations:**

- There's no IO monad. Effects are inferred, and `pure fn` lets you ask the compiler to enforce purity.
- A State monad can be defined, and **[gc]** it has none of no-GC moxie's limits. `ref` threading is still the simple way to carry state.
- Type constructors take at most one "hole" (`Result[_, E]`), and type lambdas (`[A] -> Result[String, A]`) fix any argument. Matching on types and recursion at the type level are covered in superpower 24.
- Evaluation is eager, apart from `lazy` parameters and streams, and nothing is memoized for you.
- The compiler doesn't check the monad laws.

**Where you'll actually bump into them.** Here's what the compiler says (the messages are approximate):

```
factor = 5
ops = Dict[String, (Int) -> Int]()
ops(double) = (n): n * 2        // fine: captures nothing
ops(scale) = (n): n * factor    // fine in moxie/gc: a closure in a Dict

fn pick(flag: Bool, a: Int, b: Double) (Int) -> Int:
  if flag:
    (n): n + a                  // captures an Int
  else:
    (n): n + cast[Int](b)       // fine in moxie/gc: same type, (Int) -> Int

pure fn noisy(w: Int) Int:
  println("w is $w")               // error: pure fn calls println
  w
```

**[gc]** In no-GC moxie the two lines marked "fine in moxie/gc" are errors. They are the price of having no heap: a closure's size depends on what it captures, so it can't live in a slot of fixed size, and a function returns exactly one closure type. With a collector, a function type is just its signature, so closures can be stored anywhere and a function can return a different one from each branch. Only the last error, the `pure fn`, is left.

## 18. Fibers, channels, and daemons

A fiber is started for the entry file and with `run`. Here's a complete run routine:

```
fiber fn greeter(tx: ChanW[String]) Unit:
  \write(tx, "hello from a fiber")

rx, tx = Chan[String][1]()
\run greeter(tx)
println(read(rx).get_or("nobody home"))
```

Output: `hello from a fiber`. `Chan[String][1]()` makes a channel (the element type, then room for one waiting value) and returns the channel's read and write ends as its result. `run greeter(tx)` starts the fiber and moves the write end to it, and the `\` acknowledges the `Result` that `run` returns: a statement that starts with `\` evaluates the rest of the line and throws the value away, which is how you say a `Result` is deliberately ignored. Meanwhile, `read(rx)` parks the main fiber until the greeter has written.

**Who runs when.** Starting a fiber doesn't pause the one that started it. The starter keeps going until it parks, and only then does another fiber get a turn:

```
fiber fn worker(tx: ChanW[String]) Unit:
  println("worker: started")
  \write(tx, "worker: done")

rx, tx = Chan[String][1]()
\run worker(tx)
println("runner: still going after run")
println("runner: about to read (parks)")
println(read(rx).get_or("nobody home"))
```

Output:

```
runner: still going after run
runner: about to read (parks)
worker: started
worker: done
```

The worker doesn't start until the main fiber reaches `read` and parks. Fibers interleave at park points like goroutines do, but only one runs at any moment, so a long calculation in one fiber holds up the rest until it parks. Running fibers truly in parallel would take a multi-core scheduler, which moxie doesn't have yet.

**No race conditions.** Because only one fiber runs at any moment, moxie has no race conditions. Values are immutable and resources have one owner, so there's nothing for fibers to fight over, and the Atom is the only shared state, which changes only by swapping in a new value.

**Futures.** A channel carries a stream of values. A future carries exactly one, delivered at some point. `Future[T]()` returns two handles, a read end and a write end, just as a channel does. One fiber completes the future through the write end, and anyone holding the read end can look at it:

```
fiber fn compute(w: FutureW[Int]) Unit:
  sleep(10ms)
  resolve(w, 6 * 7)

fiber fn fail(w: FutureW[Int]) Unit:
  reject(w, Error(7, "no luck"))

fn show(label: String, f: FutureR[Int]) Unit:
  when @f:
    Pending -> println("$label: pending")
    Resolved(v) -> println("$label: resolved $v")
    Rejected(e) -> println("$label: rejected ${e.message}")

r1, w1 = Future[Int]()
r2, w2 = Future[Int]()
\run compute(w1)
\run fail(w2)
show("compute", r1)
sleep(50ms)
show("compute", r1)
show("compute again", r1)
show("fail", r2)
```

Output:

```
compute: pending
compute: resolved 42
compute again: resolved 42
fail: rejected no luck
```

- **Three states.** A future starts `Pending` and leaves that state exactly once, becoming `Resolved(value)` through `resolve(w, value)` or `Rejected(error)` through `reject(w, error)`. Both consume the write end, so a future can't be completed twice.
- **Looking never waits.** `@f` takes a snapshot and returns immediately, and asking again gives the same answer once the future is settled. There is no `await`. The example above sleeps before the second look; a program that needs to wait for a result usually sends it over a channel, or parks in a loop of its own.
- **A write end that goes away rejects.** If the write end is dropped without ever being completed (say its owner finished without completing it), the future becomes `Rejected` with the reserved error `ABANDONED`, so a reader is never left looking at `Pending` forever.
- **Futures aren't atoms.** An Atom is a cell you can keep replacing, while a future is filled once and then frozen. **[gc]** Like atoms, channels, and timers, futures can be created anywhere, loops and recursion included. (In no-GC moxie the compiler counts them at startup, so they can't.)

Servers don't end, so moxie has a place for that—`daemon:` is the server program's main cycle. **[gc]** Strings built inside a cycle are reclaimed by the collector once nothing refers to them, so a program can run for years without growing, as long as it doesn't keep adding to a structure forever.

```
daemon:
  counter = select:
    case msg = read(inbox) ->
      println("got: $msg")
      break daemon
    case read(timeout) ->
      println("timed out")
      break daemon
    else:
      sleep(100ms)
      counter + 1
```

Around it, you get Go-style channels, `select`, timers, futures, atoms, and fibers. The compiler checks all of it: a channel end moves to one owner, and `clone(end)` is how you request another handle. **[gc]** They live on the heap, so you can create them wherever you like, loops included. (In no-GC moxie the compiler tallies them, so the Runtime can allocate them all up front.)

## 19. Run routines

In most FP languages, starting concurrent work takes machinery. In Haskell you reach for `forkIO` and an `MVar` (or a library like `async`), and it all lives in `IO`. In Scala, cats-effect and ZIO give you fibers, but as values you build inside an effect type and run later. Clojure brings `core.async` and its `go` blocks, and Kotlin and Rust bring `suspend` and `async`/`await`, with scopes or executors to set up first.

In moxie, you write `run` and that's it. Here are three fibers computing squares at once, each writing its answer to the same channel:

```
fiber fn square(n: Int, out: ChanW[Int]) Unit:
  \write(out, n * n)

rx, tx = Chan[Int][3]()
\run square(2, clone(tx))
\run square(3, clone(tx))
\run square(4, move tx)
total = read(rx).get_or(0) + read(rx).get_or(0) + read(rx).get_or(0)
println("$total")
```

Output: `29`. The fibers may finish in any order, and the sum is 4 + 9 + 16 either way. `clone(tx)` makes another handle for the same channel, and `move tx` hands over the last one to the new fiber.

A short fiber can also be written inline, right where you start it. The full form takes two lists: first the fiber's arguments, then the parameters to pass in. When an argument is just a name that matches the parameter name, you give that one list once:

```
rx, tx = Chan[String][2]()
tx2 = clone(tx)
// short form: parameter tx gets the variable tx
\run fn (tx):
  \write(tx, "short form")
// full form: arguments, then parameters
\run fn ("long form", tx2)(msg, out):
  \write(out, msg)
println(read(rx).get_or("none"))
println(read(rx).get_or("none"))
```

Output: `short form`, then `long form`. A literal or any other expression needs the full form.

Here's what you don't need: no `async`/`await` keywords, no IO monad to thread through your code, no executor or thread pool to configure, no locks, and no promises to chain. To wait for a fiber, just read from a channel it writes to.

The fine print:
- **Fibers are created on demand.** **[gc]** No slot is reserved in advance. A fiber function can declare a cap (`fiber[3] fn`), the Manifest can set a default cap, and `run` returns `NO_SLOT` only when a cap is full. Without a cap, `run` always succeeds.
- **Arguments are shared or moved.** **[gc]** Any value that isn't a resource is fine, closures included, and since values never change, sharing them is safe. Channel ends and write handles move. `ref` arguments and Timers aren't allowed.
- **Cancelling is a request.** A `Cancel` token is passed to the fiber, which ends itself when it sees the token in a `select` arm or a check. Nothing is killed mid-statement, and a fiber that never looks keeps running.
- **Everything shares one thread.** A long computation in one fiber holds up the others until it parks.

## 20. The outside world

Moxie programs read, write, and call C, and every one of those goes through a value you can see.

**Standard streams are values.** `stdin`, `stdout`, and `stderr` can be passed to functions, so code that prints can be tested with something else, and `with_stdin` feeds a test its input:

```
fn greet(out: Io, name: String) Unit:
  println(out, "hello, $name")
greet(stdout, "mixer")
name = with_stdin("Ada\n", fn (): read_line().get_or("nobody"))
println("hi $name")
```

**Files and sockets are the same kind of value.** `open_file`, `read_file`, `write_file`, `connect`, `listen`, and `accept` give back an `Io` (or a `Result` holding one), and `read_line`, `lines`, and `println(io, x)` work on any of them. A read waits in its own fiber only, so a server and its clients can be fibers of one program. A file or a socket is a resource and should be closed, but there are no pools to size in moxie/gc: the runtime closes whatever is still open when the program ends. UDP is the one exception to "same kind of value": a datagram is not a stream, so `bind_udp`, `send_to`, and `receive` work on a `Udp` and give back whole packets.

**Permissions are granted when you run.** A program can reach `fs.read`, `fs.write`, `net.connect`, `net.listen`, `ffi`, `stdin`, and `env` only if it was given them, in the manifest or on the command line (`moxie --allow-read=data run report.mxi`). A call outside the grant returns `Err` with the code `DENIED`, and the compiler follows the permissions through function calls the way it follows effects, so a missing grant is a compile error, not a surprise at run time:

```
[permissions]
fs.read = ["data/"]
net.connect = ["example.com:443"]
```

**C libraries are a declaration away.** A `foreign` block gives the signatures, each marked `pure`, `parks`, or `impure`, and the call looks like any other. Arrays of numbers, out-parameters, text, callbacks (even `qsort`'s comparator), handles that must be closed, and callbacks that C keeps and calls from its own thread are all covered, and `moxie bindgen` writes the declarations from a C header:

```
foreign "c":
  impure fn qsort(
    ref base: Array[Int32],
    n: UInt = len(base),
    size: UInt = size_of(base),
    cmp: (Ptr[Int32], Ptr[Int32]) -> Int32
  )
xs = Array(5i32, 3i32, 9i32, 1i32, 7i32)
qsort(ref xs, (a, b): a - b)
println(xs)
```

The output is `Array(1, 3, 5, 7, 9)`. Foreign code is outside moxie's guarantees, so the convention is a small moxie wrapper around each call. The Guide's sections 20a to 20d go through all of it.

## 21. Resources have one owner

A channel end, a timer, a future, a file, a socket, a child process, a terminal, or a handle from a C library is a resource: a value with an identity, not just a number or a piece of text. You can't copy a file the way you copy an `Int`, so moxie doesn't try. A resource has exactly one owner at a time, it moves rather than copies, and a tuple that holds one is a resource too. Where a language with a collector would tidy up later, moxie closes things at a place you can see, and the compiler checks it. There's no borrow checker to feed with lifetimes and no `&` to write. There is one rule, with two cases:

```
fn put_one(out: ChanW[Int]) Unit:
  \write(out, 1)

fn finish(out: ChanW[Int]) Unit:
  close(out)

rx, tx = Chan[Int][4]()
put_one(tx)
put_one(tx)
finish(move tx)
println("${read(rx).get_or(0)} ${read(rx).get_or(0)}")
```

Output: `1 1`. A function that only *uses* a resource, like `put_one`, borrows it for the call, and you keep it. A function that closes it, passes it on, or returns it, like `finish`, *takes it over*, and then the call says so with `move`, and the name is gone afterward. The compiler works out which functions take over, so you never declare it. Forget the word and you hear about it:

```
finish(tx)   // error: `finish` takes ownership of `tx` (it closes it, moves it,
             // or returns it), so write `finish(move tx)`; after that call, `tx` is gone
```

**Loops are where it bites.** A loop runs its body again, and a resource that moved the first time round isn't there the second time. So the compiler refuses a move that could be followed by another trip round:

```
for i in 1..=3:
  finish(move tx)   // error: `tx` is moved inside a loop; a resource may be
                    // moved only on an exiting path
```

A move is fine on a path that leaves the loop (a `break`, a `return`, a `?`). The same goes for a fiber: `run worker(tx, i)` always moves `tx` to the new fiber, which closes it when it ends, so doing that inside a loop is an error too ("handed to the new fiber inside a loop"). The way through is `clone`, which makes another handle for the same channel, and it's allowed in a loop only to feed a `run` whose fiber function has a declared limit:

```
fiber[3] fn worker(out: ChanW[Int], n: Int) Unit:
  \write(out, n)

rx, tx = Chan[Int][4]()
for i in 1..=3:
  \run worker(clone(tx), i)
close(tx)
println("${read(rx).get_or(0) + read(rx).get_or(0) + read(rx).get_or(0)}")
```

Output: `6`. The limit (`fiber[3]`) is what lets the compiler count the handles before the program starts. That is also why atoms, channels, timers, and futures can't be *created* inside a loop or recursion: every one of them takes a slot in a pool sized up front. A resource with an explicit close, bound to a name and released in the same scope, is gone before its loop goes round again.

None of this costs anything at run time. It's all decided by the compiler, so there are no reference counts and no collector to run, which is the same reason moxie/gc keeps these rules exactly as they are.

## 22. Effects you never write

Haskell tracks effects by putting them in the type: an `IO` function can't hide inside a pure one. Koka and Scala's effect libraries do something similar with more machinery. Moxie tracks them too, but you don't write them, and nothing threads through your types. The compiler works out what each function does: it prints, it waits (parks) on a channel or a timer, it uses a resource, or it uses the system (`cwd()`, `hostname()`). A caller inherits what its callees do, all the way up:

```
fiber fn square(n: Int) Int:
  n * n

fn log_square(n: Int) Int:
  println("squaring ${n}")
  square(n)

fn report(n: Int) Unit:
  println(log_square(n))

pure fn area(w: Int, h: Int) Int:
  w * h

report(3)
println(area(2, 5))
```

Output: `squaring 3`, `9`, and then `10`. Nothing above declares an effect, and adding a `println` while you debug never means editing a caller. When you *want* the compiler to hold you to something, you say so before `fn`: `pure`, `prints`, `parks`, or `impure` for "does something". A declaration is an agreement checked in both directions:

```
pure fn total(n: Int) Int:
  log_square(n)        // error: pure fn 'total' prints (calls 'println')

prints fn quiet(n: Int) Int:
  n * 2                // error: fn 'quiet' is declared prints but never does

pure fn peek(a: Atom[Int]) Int:
  @a                   // error: pure fn 'peek' uses a resource (calls '@')
```

The compiler rejects a body that does more than it declared, and it rejects a declaration the body no longer earns, so a stale `prints` can't linger after the print is gone. An interface member can be declared the same way, and then the declaration is an upper bound: an impl may do less, never more, and code that calls through the interface is checked against it. Debugging output (`dbg`, `trace`) is exempt and is removed from release builds, but `println` is real output and counts.

Purity isn't only a label. `swap`, `debug_assert`, contract conditions, and the compile-time evaluation of your own functions (superpower 24) all require a pure function, with or without the word. That's what lets the compiler run your code while it checks your code.

Effects say what code *does*. Permissions (superpower 20) say what a program is *allowed to reach*. The two meet at the edges: a call that uses the system is an effect, and whether it may touch the file system or the network is a permission the program was given.

## 23. Contracts

A contract states what a function needs and what it promises, in the code instead of a comment. `requires` is a precondition the caller must meet, `ensures` is a postcondition the function guarantees (it may name `result`), and `invariant` is a condition every value of a tuple type must satisfy:

```
tuple Account:
  owner: String
  balance: Int
  invariant balance >= 0

fn withdraw(a: Account, amt: Int) Account:
  requires amt > 0
  ensures result.balance == a.balance - amt
  Account(owner: a.owner, balance: a.balance - amt)

acct = Account(owner: "ada", balance: 50)
println(withdraw(acct, 20).balance)
```

Output: `30`. Because values never change, an invariant only needs checking where a value is built (a constructor call, a rebuild, a field update, `read`), so every `Account` that exists satisfies it. Contracts are for bugs, not for expected failures; an expected failure still returns a `Result`. When one fails the program aborts, and the message says whose fault it was:

```
println(withdraw(acct, 0).balance)
// compile error: this call to `withdraw` always fails its precondition `amt > 0` (amt = 0)

println(withdraw(acct, 80).balance)
// abort: invariant of Account failed: balance >= 0 (supplier bug)

go(0)    // where go calls withdraw(acct, n) with n = 0 at run time
// abort: requires failed in withdraw: amt > 0 (caller bug)
```

- **Blame.** A failed `requires` is a caller bug. A failed `ensures` or `invariant` is a supplier bug.
- **Caught early when it can be.** A `requires` whose arguments are all constants and that fails is a compile error, the same way a constant index out of range is.
- **Debug and release.** Contracts are checked in debug builds and in `moxie test`, and `moxie build --release` removes them (as it does `debug_assert`) unless the manifest keeps them.
- **Interfaces own the contract.** A contract on an interface member binds every impl, and an impl may not add contracts of its own, so generic code gets the promise through the interface.
- **Conditions are pure.** A condition may call only pure functions, which is the previous section at work.
- **With property tests.** `moxie test` checks contracts, so a `forall` block that generates inputs is trying to break your `ensures` lines.

Eiffel made contracts famous. In moxie they sit beside the types, and the checker uses what it can see at compile time before the run-time check ever has to fire.

## 24. Type-level programming

Most languages let you write functions on values. Moxie also lets you write functions on *types*, and run them while the compiler checks your program. A type alias whose body is a `when` is a function that takes a type apart and builds another, with an arm for each shape:

```
type alias Elem[T] = when T:
  List[X] -> X
  Array[X][N] -> X

type alias Concat[A, B] = when A:
  () -> B
  (H, ...T) -> (H, ...Concat[T, B])

type alias Length[T] = when T:
  () -> 0
  (H, ...Rest) -> 1 + Length[Rest]

tuple User:
  id: Int
  name: String

type alias Get[R, K] = when R:
  (K: T, ...Rest) -> T
  (_: _, ...Rest) -> Get[Rest, K]

fn big(n: Int) Bool:
  n > 3

type alias Pad[N] = when N:
  M if big(M) -> Array[Int][M]
  M -> Array[Int][3]

first: Elem[List[String]] = "ada"
row: Concat[(Int, String), (Bool,)] = (1, "a", true)
sized: Array[Int][Length[(Int, String)]] = Array(1, 2)
name: Get[User, "name"] = "Ada"
grid: Pad[5] = Array(1, 2, 3, 4, 5)
println("${first} ${row} ${sized} ${name} ${grid}")
```

Output: `ada (1, "a", true) Array(1, 2) Ada Array(1, 2, 3, 4, 5)`. Change any of those annotations to the wrong type and the compiler stops at that line. What you get:

- **Matching on types.** The first arm that matches wins. A bare name in a pattern, like `X` or `N`, is a variable the match fills in; `_` matches anything, and `X: Show` matches any type that implements `Show` (or `X: Show + Eq`, both).
- **Recursion, with no restriction on it.** `Concat` joins two tuple types and `Length` counts the items of one, because an alias may call itself. Since a loop that never ends would hang the compiler, each use has a budget of reductions (`type_fuel` in `Moxie.toml`, 64 by default), and an alias that calls itself on something that doesn't get smaller gets a warning.
- **Tuples taken apart.** `(H, ...T)` splits a tuple type into its first item and the rest, the type-level twin of `(first, ...rest)`, and a result can splice one back in.
- **Numbers and strings are types.** `0`, `1 + Length[Rest]`, `Array[X][N - 1]`, and `"name"` all work where a type goes. That is how a size can be computed and how `Get[User, "name"]` finds a field by its name: field names stay in tuple types, and `(K: T, ...Rest)` looks one up.
- **Guards, and your own functions at compile time.** An arm may carry `if`, and the guard can call any pure function you wrote (`big(M)`), even one from an imported package. The same goes for a size or a constant: `Array[Int][fib(10)]` is worked out by the compiler, in a sandbox with no permissions and a step limit, and a call that aborts there is a compile error.
- **Types that belong to a value.** An `any Container` hides its type, so each one has an `Item` of its own: `to.put(from.first())` is an error when `to` and `from` are different values, even if both hold the same kind of container. `a.Item` names it, with no new syntax.
- **No cost, and no run-time rule.** Type functions exist only while the compiler checks; they leave nothing in the program, like every other type.

Scala does much of this with implicits and inline code, and C++ with templates. In moxie it is the same `when` you use on values, one pass, with the same error messages as the rest of the checker.

## 25. FCFX

This is the one the whole language is built around.

**Fast compilation.** The grammar is context-free, and the compiler parses and type-checks in a single pass. There are no macros to expand and no bytecode step. The whole program is linked statically from source, with everything unreachable pruned.

**Fast execution.** Take the humble `map`:

```
a = numbers |> to_stream() |> map(_ * 2) |> take(3) |> sum()
```

In most languages, that line allocates iterators or intermediate collections and calls through function objects. In moxie, it should compile to roughly the loop you'd have written in assembly by hand. The reasons, at the highest level:

- **Streams fuse.** A stream is a source plus an index range, with stages nested around it. The terminal (`sum` here) fuses the whole chain into one flat loop, and one element at a time travels through the entire pipeline with no buffer in between.
- **Everything is specialized.** The compiler builds a copy of each generic function for each concrete use, with the lambda inlined. There's no boxing, no run-time type information, and no call through a table.
- **Allocation is cheap and short-lived.** **[gc]** Scalars and small fixed-size values live in stack frames, and a lazy stream is a small record. What does go on the heap (strings, the contents of collections, closures) mostly dies young, which is what a generational collector is built for.
- **A garbage collector built for short pauses.** **[gc]** It works in bounded slices at points where a fiber parks or allocates. Only one fiber runs at a time and values never change, so ordinary code needs no write barrier. The pauses are short, not zero, and a collector costs some memory overhead and some time that no-GC moxie doesn't pay.

The price is code size (each specialization is its own copy), the collector's overhead **[gc]**, and a few limits, which the next section lays out.

# What moxie can't do, and why

## Constraints from the "1-pass compiler"

These come with the territory, and we don't mind them. **[gc]** (In no-GC moxie this section is "Constraints from 'no GC' and '1-pass compiler'," and it has more entries. The ones that went away are listed below.)

- **No import cycles,** and names must be declared before they're used (with `forward fn` for mutual recursion). A single pass needs definitions first.
- **A function passed to `swap` can't park or block.**
- **`any` values can't be compared,** because `Self` as a parameter can't be dispatched when the type is hidden.
- **Fibers can't receive `ref` arguments.**
- **Floats can't be Dict keys.**

## What the collector costs **[gc]**

Taking the garbage collector back isn't free, and these are the prices:

- **Pauses.** They are short, because the collector works in small slices, but they are not zero.
- **Memory overhead.** A collector needs some room to work in, and some memory sits uncollected until its turn comes.
- **Leaks are possible again.** The collector frees only what nothing can reach, so a structure that keeps growing keeps its memory.
- **A full heap ends the program.** There is one heap for all fibers, so when it fills, the whole program stops with a diagnostic.
- **Updating an `Array` copies it.** Persistent structures make `List`, `Dict`, and `Set` cheap to update, but an `Array` is a flat block.
- **Resources still have one owner and move.** With a collector you can't tell when a handle dies, so ownership is what gives a close a known moment. Moxie/gc keeps the rule, and it has no finalizers.

## Constraints that went away with the GC **[gc]**

No-GC moxie has each of these because it has no heap. moxie/gc doesn't:

- **Capturing closures can be stored anywhere:** in a Dict, a tuple field, or a channel element.
- **A function can return a different closure from each branch.**
- **Streams can be returned,** unless they borrow a resource.
- **Atoms, channels, timers, and futures can be created in loops and recursion.**
- **Capacities aren't fixed.** `List`, `Dict`, and `Set` grow, and a declared size is only a hint. A channel's capacity is still declared, since it says how far a writer can run ahead of its reader, and `#unbounded` is the explicit way to ask for no limit.
- **A runtime string lasts as long as anything refers to it,** so it can be carried through a `daemon:` cycle.
- **State monads over runtime-length data work.**
- **No `String[n]`, no `static` strings, and no S-space or T-space.**
- **A loop can build a growing string or list by rebinding.** `reduce` is still the better style.


## Constraints we chose

These aren't forced on us, and each can be argued with. Here's the reasoning behind each one.

- **No orphan impls.** An impl lives with the type or the interface, so it's never ambiguous which one applies.
- **One hole in partial type application.** `Result[_, E]` is plenty, and it keeps type inference simple.
- **Operators aren't values, and there are no operator sections.** Write a lambda or a placeholder call instead; it's clearer and needs no new rules.
- **No mixing `_` and `_1` in one partial call.** The two numbering schemes together read like a puzzle.
- **Unused imports and module-level rebinding are errors.** The link report stays honest, and a program's top-level names stay stable.
- **A fiber abort still ends the whole program.** `scope:` waits for and cancels fibers, but it doesn't contain a fault, so one bad fiber isn't quietly dropped.
- **Bounded-integer arithmetic yields plain integers.** Adding two `Int[0..=100]` values can leave the range, so you say when to narrow it again.
- **Transactions don't nest.** It keeps the commit-or-roll-back rule simple to state.
- **Delegates apply only to declared tuple fields.** The field's layout has to be known.
- **Permissions belong to the program, and a package can be given less.** By default a dependency has the program's rights. A `[permissions.packages.NAME]` table in `Moxie.toml` sets a ceiling for code written in that package, and the compiler checks the whole package against it.
- **Foreign code is trusted.** The compiler cannot look inside a C library, so a `foreign` declaration is taken at its word, and a library that is granted runs with all the rights of the process.
- **`ref` and `lazy` can't be combined.** One copies in and out, and the other re-runs the argument on every read, so they pull in opposite directions.

And so it goes.

Welcome to moxie!
