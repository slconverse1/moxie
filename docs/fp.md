---
layout: default
title: "FP Overview · Moxie"
---
# FP Overview

This page explains the functional ideas that moxie is built on, in general terms, and then says how moxie does each one. Every section links to the Mixer's Guide lessons that show it in code.

## 1. Values and functions

### 1.1 The basics

**a. Values, not variables.** A value never changes once it exists. Writing `x = 5` states that `x` is 5 from then on, as in a proof. A new value gets a new name, and "updating" something means building a new value and rebinding a name to it: `p.score += 10` rebuilds `p`, and `list += 4` builds a longer list. Names can be rebound, but values cannot change. See *[Values and names](learn/03-values-and-names.html)* and *[Lists](learn/15-lists.html)*.

**b. Expressions, not statements.** Most things produce a value: an `if`, a `when`, a block. You combine values into bigger values instead of changing them step by step. See *[Truth and choices](learn/06-truth-and-choices.html)*.

**c. Functions as values.** A function can be stored, passed and returned like any other value. A function that takes or returns a function is called higher-order. See *[Functions](learn/08-functions.html)* and *[Anonymous functions and closures](learn/09-lambdas-and-closures.html)*.

**d. Closures.** A function can remember the names around it where it was written. The captured values are copied, and that captured data travels with the function. A closure can capture plain data, but not a resource with one owner such as a channel end or a file. See *[Anonymous functions and closures](learn/09-lambdas-and-closures.html)*, and section 4 for where closures can be stored.

**e. Pattern matching.** Instead of a chain of `if`s that test a value's shape, you write one case per shape and the compiler checks that the cases cover them all. See *[Patterns](learn/19-patterns.html)* and *[Binary patterns and type tags](learn/51-binary-patterns-and-type-tags.html)*.

**f. Names and binding order.** Read `x = 5` as a statement of equality, not as a box that changes. Some rules about names follow from that. A function sees only the names bound above it in its file, and what it saw stays what it saw. A function can call only functions declared above it, and two that call each other need a `forward fn` signature first; the same goes for types, with `forward tuple` or `forward enum`. The top level of a library file is module level: each name is bound once and every function below can read it. The top level of the entry file behaves like the body of `main`, so `x = 5` followed by `x += 1` is ordinary rebinding. Inside a function a local may reuse a module-level name, which hides it. Two more tools reach outer bindings: `total@1` names the nearest enclosing binding of `total`, and an `in` line at the start of a block starts a local copy of an outer variable without changing the outer one. See *[Values and names](learn/03-values-and-names.html)* and *[Functions](learn/08-functions.html)*.

**g. Recursion, tail calls and loops.** Without changing variables, a loop becomes a function that calls itself. A call in tail position, where nothing is left to do after it returns, can reuse the same stack space, so the recursion can run as long as it needs. Moxie makes a tail call reuse the frame, and `tailrec` makes the compiler check that a recursion really is a tail call. A loop and a tail-recursive function are two ways of writing the same thing. See *[Recursion and function clauses](learn/10-recursion-and-clauses.html)* and *[Loops](learn/07-loops.html)*.

### 1.2 Values and functions (advanced)

**a. map, filter and fold.** These three replace most explicit loops over a collection. `map` transforms each element, `filter` keeps some, and `fold` (called `reduce` in moxie) combines them into one value. See *[Lists](learn/15-lists.html)* and *[Pipelines and streams](learn/21-streams-and-pipelines.html)*.

**b. Composition and pipelines.** Composition joins two functions into one. Moxie's operators for this, which you will see in the lessons:

- `~>` is forward composition: `f ~> g` means "apply `f`, then `g`."
- `|>` is the pipe: `xs |> f()` passes `xs` into `f` as its first argument.
- `|>>` is bind, `<$>` maps a plain function over a value in a container, and `<*>` applies a function held in a container to a value in one.
- `&` and `_` are placeholders: `_` marks where a value goes in a call, so `map(double, _)` is a function that waits for its list.

Because `~>` applies stages in the order written, backward composition is written by reversing the stages. For mathematical order, `compose` takes any number of functions and applies the last one first: `compose(f, g, h)(x)` is `f(g(h(x)))`. A chain of functions passed to `compose` must all take and return the same type. See *[Values, purity, and composing functions](learn/36-purity-and-composition.html)* and *[Pipe slots and caching](learn/50-pipe-slots-and-caching.html)*.

**c. Purity and effects.** A pure function returns the same result for the same arguments and does nothing else. Effects such as printing, reading a channel or swapping an `Atom` are part of what a function does, and the compiler works out which functions have them. `pure fn` asks the compiler to check that a function has none. A `pure fn` may still contain a `mutable` block (section 3f), because nothing inside it can be seen from outside. See *[Values, purity, and composing functions](learn/36-purity-and-composition.html)*.

**d. Laziness and evaluation order.** Moxie is eager by default, so laziness is something you ask for, in two places. The first is streams. A stream is a recipe, a source plus a list of stages, and nothing happens until a terminal (`collect`, `sum`, `reduce`, `count`, or a `for` loop) pulls on it. Horizontal stages such as `map`, `filter`, `take`, `scan` and `enumerate` are lazy: one element travels through the entire chain, and an element that `take` or `filter` rejects is never mapped over further. That is why an infinite source costs nothing, and a pipeline does only the work its consumer asks for. Vertical stages such as `sort` and `reverse` must see every element first, so they collect them in a buffer. The second place is `lazy` parameters, in section e below. Nothing is memoized for you. See *[Pipelines and streams](learn/21-streams-and-pipelines.html)* and *[More stream tools](learn/61-more-stream-tools.html)*.

**e. How arguments are passed.** A function has four ways to receive an argument, and moxie supports most of them.

- **By value** is the default. The argument is evaluated once, before the call, and the function gets its own value. Nothing it does can change your variable.
- **By reference** is for a parameter marked `ref`. It isn't a shared pointer. The function gets a copy, may rebind it, and when the function returns, the final value is copied back into the caller's variable. Both sides say so: the parameter is declared with `ref`, and the caller writes `ref` in front of the variable, so a change to your variable is always visible at the call. A `ref` parameter the function never changes draws a compiler warning.
- **By name** is for a parameter marked `lazy`. The argument isn't evaluated before the call. It is evaluated each time the function reads the parameter, and never if the function never reads it. That makes `lazy` the right tool for a fallback value or an expensive default that is needed only sometimes. A lazy argument can't contain a `ref`.
- **By need** is by name with a cache, so the argument is evaluated at most once. Moxie doesn't build this in. If you want it, read the lazy parameter once, bind the result to a name, and use that name.

See *[Functions](learn/08-functions.html)*.

**f. Monads and sequencing.** Chains of steps that can each fail are the classic functional problem. Imagine three lookups that each return a `Result`, with every step checking the one before. Written with nested `when`s, the real work ends up far to the right under a stack of closing brackets: the pyramid of doom. Moxie gives you several ways to flatten it, and all of them keep the compiler's checks:

- **`?` hands the failure back.** A `?` after a call means "if this failed, return the error to my caller; otherwise give me the value." The same function becomes flat lines, and every error still reaches the caller.
- **Let-else is a guard clause for a pattern.** When a value has to have a particular shape, `Active(_, rank) = acct else fail(7, "account closed")` binds the pieces and bails out on the spot if the shape is wrong.
- **A `for` comprehension chains steps that depend on each other.** Each line can use the names bound above it, and the first failure ends the chain.
- **`|>>` is bind.** It runs the next step on the value inside, and stops at the first failure. It's the right choice when each step needs only the result of the one before it. `<$>` and `<*>` combine independent inputs, with the first failure winning.

The operators work for any type with the right impls. The prelude gives you the `Functor`, `Applicative` and `Monad` interfaces, with ready-made instances for `Result`, `Stream`, `List` and `Array`. Types such as `Maybe`, `Option`, `Either`, `State` and parser types are not built into the language or its library. For any other type you define the type and write its `impl Monad[...]`, and then `|>>`, `<$>`, `<*>` and `for` work on it. Code can be written once for every monad, as `fn double_in[F[_] Monad](m F[Int]) F[Int]` shows: it works for `Box.Full(21)` and `Ok(21)` alike. See *[Functors and monads](learn/37-functors-and-monads.html)*, *[For comprehensions](learn/38-for-comprehensions.html)*, *[Missing values and failures: Option and Result](learn/14-missing-and-failed.html)* and *[Transformers](learn/63-transformers.html)*.

### 1.3 Iterators, generators and comprehensions

Iterating over data is the everyday work of functional code, and moxie has three ways to do it.

**Iterators.** Any collection is a loop source: `for x in numbers` walks a list. A `Dict` yields `(key, value)` tuples, a `Range` counts, with a step and a downward step (`3..1 step -1` counts 3, 2, 1), and `zip` pairs two sources. Your own tuple or enum is a source too, once it has a `to_stream` function that returns a `Stream[T]`. A stream (`to_stream()`) is moxie's general iterator, and `map`, `filter`, `take`, `scan`, `enumerate`, `windows` and their relatives are its stages. See *[Pipelines and streams](learn/21-streams-and-pipelines.html)* and *[More stream tools](learn/61-more-stream-tools.html)*.

**Generators.** A generator is a function that returns a stream built with `unfold`. The step takes the current state and returns a value together with the next state, or an `Err` to stop. The first pass receives the seed, and each later pass receives the state the previous pass returned. A sequence such as the Fibonacci numbers can be infinite, and `take` is what ends the loop. Since the step never returns an `Err`, the stream never ends on its own. See *[More stream tools](learn/61-more-stream-tools.html)*.

**Comprehensions.** `List`, `Set` and `Dict` each have a comprehension form that builds a collection from a source, with one `if` filter allowed and no nested `for`. The collection's size comes from its declared type. See *[Lists](learn/15-lists.html)*, *[Arrays](learn/16-arrays.html)* and *[Dicts and sets](learn/17-dicts-and-sets.html)*.

**`for` comprehensions.** The block form comes from Scala's `for`/`yield`, widened with ideas from F# computation expressions. It chains steps that can each fail or come up empty, and it stops at the first one that does. It works for `Box`, `Result`, streams, and any other type with the right interfaces. A line `name = expr` binds a value, and a line that has to match a pattern uses a let-else, as section 1.2f explains. See *[For comprehensions](learn/38-for-comprehensions.html)*.

## 2. Data and missing values

**a. Common data types.** Most FP languages share a core set of types, and moxie has them too:

- Numbers: `Int`, `Double`, `Decimal`, and sized integers such as `UInt8`. Each type's arithmetic is checked for mixing, so an `Int` and a `Double` don't combine without a conversion. See *[Numbers](learn/04-numbers.html)*.
- Strings: `String`, with interpolation such as `"hi ${name}"`. See *[Text](learn/05-text.html)*.
- Collections: `List` for ordered values, `Array` for fixed-size ones, `Dict` for key-value pairs, and `Set` for unique values. All are immutable. See *[Lists](learn/15-lists.html)*, *[Arrays](learn/16-arrays.html)* and *[Dicts and sets](learn/17-dicts-and-sets.html)*.
- Tuples, which are the structs of moxie, and enums. See the next two entries.

**b. Tuples and parameter unification.** A tuple groups named fields into one value. Moxie treats a tuple and a parameter list as the same shape: a function's parameters have the same type as a tuple of those parameter types, so a call with a single tuple argument can unpack into the parameters when the shapes match. A function can then ask for only the fields it needs, as in `(name String, ...)`, which accepts any tuple that has a `name`. A declared tuple's field can also have an inline, unnamed tuple type, written in place as in `xyz (x Double, y Double, z Double)`, so the field needs no named type of its own. The same applies to tuples built from literals: their field types are never declared, and they are shared by any literal with the same fields. See *[Tuples](learn/12-tuples.html)* and *[Functions](learn/08-functions.html)*.

**c. Enums and variants.** An enum is a value that is one of several named cases, and each case can hold its own data. A `when` over an enum must cover every case. See *[Enums](learn/13-enums.html)*.

**d. Missing and failed values.** Moxie has no `null`. A value that may be absent is an `Option`, and an operation that may fail returns a `Result`, which the compiler makes you handle. See *[Missing values and failures: Option and Result](learn/14-missing-and-failed.html)*.

## 3. Structure

### 3a. Modularity without classes

Martin Odersky, who designed Scala, has argued that the main thing object-oriented programming gives you is not inheritance but modularity: a program is built from parts that keep their insides private and show the rest of the program a small interface, so one part can be replaced without changing the others. You can have all of that without a class hierarchy. Moxie has it from four pieces.

- **An interface is the boundary.** The code that needs a logger asks for the interface, not for a particular logger. Any type that has an `impl` of the interface can be passed in, and nothing else about it is visible. Unlike a structural system (Go, TypeScript), a type joins an interface only by an explicit `impl`, so you can always find the place where it agreed to the contract, and you can add an `impl` for a type that you didn't write. A test can hand the code a fake. See *[Methods and interfaces](learn/20-interfaces.html)*.
- **`any` is dynamic dispatch without a hierarchy.** When you want a mixed collection, say `List[any Logger]`, each value is stored together with the way to call its `Logger` methods. No type is a subtype of anything. See *[Typeclasses](learn/46-typeclasses.html)*.
- **Hiding state is lexical.** Everything in moxie is immutable, so a part's private state is either a field of its tuple or something a closure captured, and the code outside can reach it only through the functions you hand out. A function can return a closure that keeps a private counter, and the counter has no name outside it. See *[Anonymous functions and closures](learn/09-lambdas-and-closures.html)*.
- **Reuse is delegation, not inheritance.** What people miss most when they give up base classes is "override one method and keep the other ten." `proxy` does that: the methods an `impl` doesn't write are forwarded to a field, and the ones it does write win. There is no base class to become fragile, no `super`, and no diamond. See *[Properties, delegates, and proxies](learn/48-properties-delegates-proxies.html)*.

Packages and imports are the outer layer of the same idea. See *[Packages and imports](learn/27-packages.html)*.

### 3b. Encapsulation without objects

An object bundles state with the methods that may touch it. Functional languages get the same protection, hidden representation and controlled change, from other tools, and moxie has all of them.

- **An opaque type protects an invariant.** An opaque type is the module-level answer to a class with private fields. Other packages can name the type and hold it, but they can't construct or inspect it, so the only way to get an `Account` is through the functions that check the rules. Outside the declaring package nobody can write `Account(...)` or read its balance, so a negative balance can't be built, and a "change" is always a new `Account` made by a function that you wrote. See *[Naming types: aliases, opaque types, and unions](learn/18-types-of-types.html)*.
- **A closure hides its captured data.** A function can capture private state and hand out only the functions that use it. The captured `Atom` or tuple field is the private part. See section 3a above.
- **State is threaded, and the compiler can hide the threading.** Where a functional program would use the State monad, moxie lets a `ref` parameter carry the state, as section 3e explains.
- **Local mutation gets a block of its own.** A `mutable` block is the one place a variable is written in place, and nothing outside it can see the writes. Section 3f explains it.
- **An existential hides the representation.** A collection of parts whose internal state types differ, such as widgets or game entities, needs each part to keep its state private while sharing a behavior. `any Interface` is that existential: the value travels with its methods, and the code that holds it can't see what is inside.

| Need | Moxie's tool | Mutability |
| --- | --- | --- |
| Enforce a rule about a value | Opaque type with `export`ed functions | Immutable |
| Hide a private counter or handle | A closure over an `Atom`, or a tuple field | Only the `Atom` |
| Thread state through a pipeline | `ref` parameters, returned tuples | Immutable |
| An in-place algorithm | A `mutable` block | Local only, never visible |
| Parts with different hidden state | `any Interface` | Immutable |

See *[Naming types: aliases, opaque types, and unions](learn/18-types-of-types.html)* and *[In-place algorithms: `mutable` blocks](learn/56-mutable-blocks.html)*.

### 3c. Interfaces and typeclasses

An interface is a set of operations, and a type joins it by writing an `impl`. An `impl` says that a type belongs to the interface, and joining adds nothing to the type itself: no fields, no hidden pointer, no parent. A type can join one interface or a hundred.

There is no data-type hierarchy and no inheritance. In an object-oriented language, a `Dog` is a kind of `Animal` by its class; in moxie, a `Dog` is whatever its tuple says, and only the interfaces it has an `impl` for can be used on it. You can implement your own interface for somebody else's type, even a built-in such as `Int`. Membership can be added after the fact and by someone else.

The language offers the rest of the typeclass toolbox. A bound names the interfaces a type must belong to, as in `[T Ordered + Equatable]`, and any member can be used, related or not. Interfaces can have default method bodies, associated types, and properties (a field that runs code, computed or lazy, with observers), and an `impl` can be conditional. Everything is specialized per use at compile time, so there are no tables at run time. See *[Methods and interfaces](learn/20-interfaces.html)* and *[Typeclasses](learn/46-typeclasses.html)*.

If you're a Haskell programmer: a class is an `interface`, an instance is an `impl`, a superclass is an embedded interface, and `Functor`, `Applicative` and `Monad` are real interfaces over type constructors.

### 3d. Generics

A generic function is written once for many types. The compiler checks each use at the type it is given, and specializes a copy for it, so nothing is looked up at run time. See *[Generic functions](learn/11-generics.html)*.

### 3e. State without mutation

A program can carry changing state in two ways that keep every value immutable.

- **Pass it along.** A `ref` parameter carries state through a call: the callee gets a copy, rebinds it, and the final value goes back to the caller's variable. The code reads like mutation while nothing is shared. Returning the state with the answer, as a tuple, does the same thing explicitly.
- **Swap an `Atom`.** An `Atom` holds an immutable value and swaps in a new one, lock-free, through a pure function, as in `swap(counter, _ + 1)`. Readers always get an immutable snapshot. The `Atom` is the only mutable state that is shared or outlives a call, so a closure that captures one is where state lasts past a single call.

Lenses let you read and update a field deep inside a value. See *[State, lenses, lazy sequences, and monoids](learn/39-state-lenses-monoids.html)* and *[Atoms and futures](learn/24-atoms-and-futures.html)*.

Resources are the exception to copying. A channel end, a timer, or a database connection is a handle with an identity, so it is moved, with one owner at a time, rather than copied. A tuple that holds a resource is a resource too.

### 3f. Local mutation, without leaks

Immutability is the rule, and it has one deliberate exception. Inside a `mutable` block you can write to your own variables in place, and nothing outside can ever tell. You get the speed and the plain loops of imperative code, and the function around the block stays pure.

Inside the block, `=` declares a variable the first time and assigns to it after that, and `x += e`, `out(i) = v` and `p.f = e` write in place from any depth of loop or branch, with no rebinding and no shadowing. The writes are guaranteed in place, so an in-place sort, a sieve or union-find costs what it should. The `algo` package is built this way.

- **Nothing leaks.** Values enter the block by copy, or by move when the old one is dead, and leave as ordinary immutable values. `b = a` inside copies, and a closure made inside takes the current values, so no mutable variable can be reached from outside. Haskell needs the `ST` monad and a rank-2 type to prove this. Moxie's other rules already guarantee it.
- **Purity survives.** The block is pure from outside, so a `pure fn` may contain one.
- **It is an expression.** The last line is the value, so a block can sit anywhere a value can.
- **The rest stays honest.** A variable keeps its declared type, and an outer name is read-only unless copied in on an `in` line. The only truly shared mutable thing is still the `Atom`.

See *[In-place algorithms: `mutable` blocks](learn/56-mutable-blocks.html)*.

## 4. Limits

Some functional patterns don't fit in moxie, or fit only with conditions. These are the ones to know.

- **There is no IO monad.** Effects are inferred from what a function does, and `pure fn` lets you ask the compiler to enforce purity.
- **Closures and storage.** A closure's size depends on what it captures, so a capturing closure can live in a `Dict`, a tuple field or a channel only with others that capture the same kinds of values. The type says so with `with`, as in `(Int) -> Int with (Int)`. A function returns exactly one closure type. Plain functions can be stored: a lambda that uses only constants, or names bound once to values known at compile time, counts as plain. Closures can always be passed, returned and composed.
- **In the GC-free dialect, a closure can't live in a tuple field.** A closure that captures values in a tuple field would leave the captured values with no owner. The record-of-functions style is written with an interface and a tuple that holds its state, as in section 3a. The `moxie/gc` dialect does allow the record-of-closures style. See *[The two dialects](learn/60-the-two-dialects.html)*.
- **A State monad can be defined only as a local value,** with no loops or recursion over runtime-length data. `ref` threading is the recommended way to carry state.
- **Type constructors take at most one hole,** as in `Result[_, E]`. Type lambdas, such as `[A] -> Result[String, A]`, fix any argument.
- **Evaluation is eager,** apart from `lazy` parameters and streams, and nothing is memoized for you.
- **The compiler doesn't check the monad laws.** It checks types and purity, but it doesn't prove that a monad you write obeys them.
