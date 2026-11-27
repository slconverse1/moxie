---
layout: default
title: "FP Overview · Moxie"
---
# FP Overview

This page explains the functional terms that moxie uses, in general terms, and then says how moxie does each one. Each term has its own section, so the Intros and Guides can link to it. Every section links to the Mixer's Guide lessons that show it in code. Terms marked *(moxie/gc)* work only in the garbage-collected dialect.

## 1. Values and functions

### Immutability {#immutability}

A value never changes once it exists. Writing `x = 5` states that `x` is 5 from then on, as in a proof. "Updating" something means building a new value and rebinding a name to it: `p.score += 10` rebuilds `p`, and `list += 4` builds a longer list. Names can be rebound, but values cannot change. See *[Values and names](learn/03-values-and-names.html)* and *[Lists](learn/15-lists.html)*.

### Expressions {#expression}

Most things produce a value: an `if`, a `when`, a block. You combine values into bigger values instead of changing them step by step. See *[Truth and choices](learn/06-truth-and-choices.html)*.

### Names and binding order {#binding-order}

Read `x = 5` as a statement of equality, not as a box that changes. A function sees only the names bound above it in its file, and what it saw stays what it saw. A function can call only functions declared above it, and two that call each other need a `forward fn` signature first; the same goes for types, with `forward tuple` or `forward enum`. The top level of a library file is module level: each name is bound once and every function below can read it. The top level of the entry file behaves like the body of `main`, so `x = 5` followed by `x += 1` is ordinary rebinding. Two tools reach outer bindings: `total@1` names the nearest enclosing binding of `total`, and an `in` line at the start of a block starts a local copy of an outer variable without changing the outer one. See *[Values and names](learn/03-values-and-names.html)* and *[Functions](learn/08-functions.html)*.

### Higher-order function {#higher-order}

A function can be stored, passed and returned like any other value. A function that takes or returns a function is higher-order. See *[Functions](learn/08-functions.html)* and *[Anonymous functions and closures](learn/09-lambdas-and-closures.html)*.

### Closure {#closure}

A function can remember the names around it where it was written. The captured values are copied, and that captured data travels with the function. A closure can capture plain data, but not a resource with one owner such as a channel end or a file. A closure can keep private state that no other code can name, which is how moxie hides state without objects (see [Encapsulation](#encapsulation)). Where closures can be stored depends on the dialect (see [Limits](#limits)). See *[Anonymous functions and closures](learn/09-lambdas-and-closures.html)*.

### Pattern matching {#pattern-matching}

Instead of a chain of `if`s that test a value's shape, you write one case per shape and the compiler checks that the cases cover them all. A pattern describes a shape and names its parts at the same time. See *[Patterns](learn/19-patterns.html)* and *[Binary patterns and type tags](learn/51-binary-patterns-and-type-tags.html)*.

### Recursion {#recursion}

Without changing variables, a loop becomes a function that calls itself. A loop and a recursive function are two ways of writing the same thing. A recursion that isn't a tail call uses one stack frame per call, and the stack is large but finite. See *[Recursion and function clauses](learn/10-recursion-and-clauses.html)* and *[Loops](learn/07-loops.html)*.

### Tail call {#tail-call}

A call in tail position is one where nothing is left to do after it returns. Moxie makes a tail call reuse the function's frame, so the recursion can run as long as it needs. The `tailrec` marker makes the compiler check that a recursion really is a tail call. Without a tail call, a deep recursion runs out of stack, and the running fiber aborts with a stack-overflow diagnostic. See *[Recursion and function clauses](learn/10-recursion-and-clauses.html)*.

### Map, filter and fold {#map-filter-fold}

These three replace most explicit loops over a collection. `map` transforms each element, `filter` keeps some, and `fold` (called `reduce` in moxie) combines them into one value. See *[Lists](learn/15-lists.html)* and *[Pipelines and streams](learn/21-streams-and-pipelines.html)*.

### Composition {#composition}

Composition joins two functions into one. `~>` is forward composition: `f ~> g` means "apply `f`, then `g`." Because `~>` applies stages in the order written, backward composition is written by reversing the stages. For mathematical order, `compose` takes any number of functions and applies the last one first: `compose(f, g, h)(x)` is `f(g(h(x)))`. A chain of functions passed to `compose` must all take and return the same type. See *[Values, purity, and composing functions](learn/36-purity-and-composition.html)*.

### Pipe {#pipe}

`|>` passes a value into a call: `xs |> f()` passes `xs` into `f`. The compiler places the piped value in the first or last mandatory parameter, whichever fits. If both fit, the call is ambiguous and you mark the slot with `&`. A middle slot also needs `&`. See *[Pipe slots and caching](learn/50-pipe-slots-and-caching.html)*.

### Placeholder {#placeholder}

`_` marks where a value goes in a call, so `map(double, _)` is a function that waits for its list. `_1` and `_2` name the first and second of two or more. Placeholders are legal only where a function type is expected or in a partial call. See *[Values, purity, and composing functions](learn/36-purity-and-composition.html)*.

### Partial application {#partial-application}

Calling a function with some arguments and leaving the rest for later. In moxie a partial call is written with placeholders: `log("ERROR", _)` is a function that takes the message, and `fn times10 = multiply(_, 10)` names it. Because every function takes its parameters as one bundle, partial application comes from the placeholder call rather than from currying. See *[Values, purity, and composing functions](learn/36-purity-and-composition.html)*.

### Currying {#currying}

A function of several arguments written as a chain of one-argument functions, so `f(a)(b)` calls it. Moxie's functions take all their arguments at once. When you want classic currying, the prelude's `curry(f)` makes a curried version of a function with any number of parameters, and `uncurry[n](g)` goes the other way. See *[Values, purity, and composing functions](learn/36-purity-and-composition.html)*.

### Purity {#purity}

A pure function returns the same result for the same arguments and does nothing else. `pure fn` asks the compiler to check that a function has no effects. A `pure fn` may still contain a `mutable` block (see [Local mutation](#local-mutation)), because nothing inside it can be seen from outside. See *[Values, purity, and composing functions](learn/36-purity-and-composition.html)*.

### Side effect {#side-effect}

An effect outside the function's result, such as printing, reading a channel, writing a file or swapping an `Atom`. Moxie doesn't promise purity everywhere: the compiler works out which functions have effects, and a `pure fn` must have none. There is no IO monad (see [Limits](#limits)).

### Referential transparency {#referential-transparency}

You can replace a call with its result without changing the program's behavior. In an expression-based language, `f(x)` yields a result, and code can be moved, refactored and tested like mathematics. In a statement-based language, moving code is risky because statements rely on when and where they change the surrounding environment. A `pure fn` is referentially transparent by the compiler's check. Other functions are transparent only when they have no side effects, which the compiler tells you.

### Laziness {#laziness}

Moxie is eager by default, so laziness is something you ask for, in two places. The first is streams: a stream is a recipe, and nothing happens until a terminal (`collect`, `sum`, `reduce`, `count`, or a `for` loop) pulls on it. Horizontal stages such as `map`, `filter`, `take`, `scan` and `enumerate` are lazy, so an element that `take` or `filter` rejects is never mapped over further, and an infinite source costs nothing. Vertical stages such as `sort` and `reverse` see every element first, so they collect them in a buffer. The second place is a `lazy` parameter (see [By name](#by-name)). See *[Pipelines and streams](learn/21-streams-and-pipelines.html)* and *[More stream tools](learn/61-more-stream-tools.html)*.

### Eager evaluation {#eager}

Arguments are computed once, before the call. Eager is the default, and the exceptions are `lazy` parameters and streams. See [Laziness](#laziness).

### Memoization {#memoization}

Storing a result so that the same call is not computed again. Moxie never caches behind your back: nothing is memoized automatically. A cache is something you write on purpose, and the lesson shows the ways to do it. See *[Pipe slots and caching](learn/50-pipe-slots-and-caching.html)*.

### By value {#by-value}

The default way to receive an argument. The argument is evaluated once, before the call, and the function gets its own value. Nothing it does can change your variable.

### By reference (`ref`) {#ref-parameter}

A parameter marked `ref`. It isn't a shared pointer. The function gets a copy, may rebind it, and when the function returns, the final value is copied back into the caller's variable. The caller writes `ref` in front of the variable, so a change is always visible at the call. A `ref` parameter the function never changes draws a compiler warning. See *[Functions](learn/08-functions.html)*.

### By name (`lazy`) {#by-name}

A parameter marked `lazy`. The argument isn't evaluated before the call. It is evaluated each time the function reads the parameter, and never if the function never reads it. A lazy argument can't contain a `ref`. See [Laziness](#laziness).

### By need {#by-need}

By name with a cache, so the argument is evaluated at most once. Moxie doesn't build this in. To get it, read the lazy parameter once, bind the result to a name, and use that name. See [Memoization](#memoization).

## 2. Data and types

### Common data types {#common-data-types}

Most FP languages share a core set of types, and moxie has them too:

- Numbers: `Int`, `Double`, `Decimal`, and sized integers such as `UInt8`. Each type's arithmetic is checked for mixing, so an `Int` and a `Double` don't combine without a conversion. See *[Numbers](learn/04-numbers.html)*.
- Strings: `String`, with interpolation such as `"hi ${name}"`. See *[Text](learn/05-text.html)*.
- Collections: `List` for ordered values, `Array` for fixed-size ones, `Dict` for key-value pairs, and `Set` for unique values. All are immutable. See *[Lists](learn/15-lists.html)*, *[Arrays](learn/16-arrays.html)* and *[Dicts and sets](learn/17-dicts-and-sets.html)*.
- Tuples and enums. See [Tuple](#tuple) and [Enum](#enum).

### Tuple {#tuple}

A tuple groups named fields into one value, the structs of moxie. A declared tuple's field can have an inline, unnamed tuple type, so the field needs no named type of its own. Tuples built from literals have their field types inferred and are shared by any literal with the same fields. See *[Tuples](learn/12-tuples.html)*.

### Unification of tuples and parameter lists {#unification}

Moxie treats a tuple and a parameter list as the same shape: a function's parameters have the same type as a tuple of those parameter types. A call with a single tuple argument unpacks into the parameters when the shapes match. Parameter modifiers such as `ref`, `lazy` and `using` have no tuple counterpart, so the unification stops there. See *[Tuples](learn/12-tuples.html)* and *[Functions](learn/08-functions.html)*.

### Product type {#product-type}

A value that holds several fields together, all present at once. A tuple is moxie's product type. See [Tuple](#tuple).

### Enum {#enum}

A value that is exactly one of several named cases, and each case can hold its own data. A `when` over an enum must cover every case. See *[Enums](learn/13-enums.html)*.

### Sum type {#sum-type}

A type whose value is one of several alternatives, as in an OR. An enum is moxie's sum type. See [Enum](#enum) and [Algebraic data types](#algebraic-data-types).

### Algebraic data types {#algebraic-data-types}

Data built by combining sum types (one of several cases) and product types (several fields together). In moxie, enums are the sums and tuples are the products. A `when` over an enum takes the value apart, and the compiler checks that every case is handled. See [Enum](#enum) and [Tuple](#tuple).

### Option {#option}

A value that may be absent is an `Option[T]`, which is either `Some(value)` or `None`. Moxie has no `null`, so the type says that a value may be missing and the compiler makes the caller handle it. See *[Missing values and failures: Option and Result](learn/14-missing-and-failed.html)*.

### Result {#result}

An operation that may fail returns a `Result[T, E]`, which is `Ok(value)` or `Err(error)`. The compiler makes you handle it. `?` after a call returns the error to the caller and otherwise gives you the value. See *[Missing values and failures: Option and Result](learn/14-missing-and-failed.html)*.

### Open type and row polymorphism {#row-polymorphism}

An open type accepts any tuple with at least the fields it names, as in `(name String, ...)`. The `...` is the rest of the row, the fields the function doesn't care about. Open types appear only in parameters and as a bound. The compiler knows the whole shape at each call and builds a copy of the function for it. See *[Open data types](learn/41-open-data-types.html)*.

### Refinement type {#refinement-types}

A type with a condition on it, written with `where` after a parameter, result or field: `i Int where i >= 0 and i < len(xs)`. The compiler checks the condition at compile time when it can, and otherwise checks it when the program runs. See *[Refined parameters: proofs in the signature](learn/49-refined-parameters.html)*.

## 3. Iterators, generators and comprehensions

### Iterator {#iterator}

A source you can loop over. Any collection is a loop source: `for x in numbers` walks a list. A `Dict` yields `(key, value)` tuples, a `Range` counts with an optional step, and `zip` pairs two sources. A stream (`to_stream()`) is moxie's general iterator, and `map`, `filter`, `take`, `scan`, `enumerate` and `windows` are its stages. Your own tuple or enum is a source once it has a `to_stream` function that returns a `Stream[T]`. See *[Pipelines and streams](learn/21-streams-and-pipelines.html)* and *[More stream tools](learn/61-more-stream-tools.html)*.

### Stream {#stream}

A lazy pipeline of stages over a source. Each element passes through the whole chain before the next one starts, so a stream does only the work its consumer asks for. See [Laziness](#laziness) and *[Pipelines and streams](learn/21-streams-and-pipelines.html)*.

### Generator {#generator}

A function that returns a stream built with `unfold`. The step takes the current state and returns a value together with the next state, or an `Err` to stop. The first pass receives the seed, and each later pass receives the state the previous pass returned. A sequence such as the Fibonacci numbers can be infinite, and `take` is what ends the loop. See *[More stream tools](learn/61-more-stream-tools.html)*.

### Comprehension {#comprehension}

`List`, `Set` and `Dict` each have a comprehension form that builds a collection from a source, with one `if` filter allowed and no nested `for`. The collection's size comes from its declared type. See *[Lists](learn/15-lists.html)*, *[Arrays](learn/16-arrays.html)* and *[Dicts and sets](learn/17-dicts-and-sets.html)*.

### For comprehension {#for-comprehension}

The block form of `for` with `yield` comes from Scala, widened with ideas from F# computation expressions. It chains steps that can each fail or come up empty, and it stops at the first one that does. It works for `Box`, `Result`, streams, and any other type with the right interfaces. A line `name = expr` binds a value, and a line that has to match a pattern uses a let-else. See *[For comprehensions](learn/38-for-comprehensions.html)*.

## 4. Structure

### Modularity {#modularity}

Martin Odersky, who designed Scala, has argued that the main thing object-oriented programming gives you is not inheritance but modularity: a program is built from parts that keep their insides private and show the rest of the program a small interface, so one part can be replaced without changing the others. You can have all of that without a class hierarchy, with four pieces: an [interface](#interface), `any` ([existential type](#existential-type)), lexical hiding of state (see [Closure](#closure)), and delegation with `proxy`, which forwards the methods an `impl` doesn't write to a field. There is no base class to become fragile. See *[Methods and interfaces](learn/20-interfaces.html)*, *[Properties, delegates, and proxies](learn/48-properties-delegates-proxies.html)* and *[Packages and imports](learn/27-packages.html)*.

### Interface {#interface}

The boundary a part of a program asks for. Code that needs a logger asks for the interface, not for a particular logger, and any type with an `impl` of that interface can be passed in. A type joins an interface only by an explicit `impl`, so you can always find where it agreed to the contract, and you can add an `impl` for a type you didn't write. See *[Methods and interfaces](learn/20-interfaces.html)*.

### Typeclass {#typeclass}

Moxie has no separate typeclass feature. A class is an [interface](#interface), an instance is an `impl`, and a constraint is a bound. A type joins one interface or a hundred, and joining adds nothing to the type: no fields, no hidden pointer, no parent. There is no data-type hierarchy and no inheritance. A bound names the interfaces a type must belong to, as in `[T Ordered + Equatable]`. Interfaces can have default method bodies, associated types and properties, and an `impl` can be conditional. Everything is specialized per use at compile time, so there are no tables at run time. If you're a Haskell programmer, a superclass is an embedded interface. See *[Typeclasses](learn/46-typeclasses.html)*.

### Existential type {#existential-type}

`any Interface` holds a value together with the way to call its methods, so a collection can hold values of different types that share an interface, and the code that holds one can't see what is inside. No type is a subtype of another. See *[Typeclasses](learn/46-typeclasses.html)*.

### Generics {#generics}

A generic function is written once for many types. The compiler checks each use at the type it is given and specializes a copy for it, so nothing is looked up at run time. See *[Generic functions](learn/11-generics.html)*.

### Higher-kinded type {#higher-kinded-types}

A type constructor, such as `List` or `Result[_, E]`, takes a type and makes a type. A function can be generic over a type constructor, as in `fn double_in[F[_] Monad](m F[Int]) F[Int]`, and then it works for every type with that interface. A *type lambda*, such as `[A] -> Result[String, A]`, fixes any argument. Moxie takes at most one hole in an ordinary type constructor. See *[Types that compute](learn/47-types-that-compute.html)*.

### Encapsulation {#encapsulation}

An object bundles state with the methods that may touch it. Functional languages get the same protection, hidden representation and controlled change, from other tools: an [opaque type](#opaque-type) protects an invariant, a closure hides its captured data, state is threaded with `ref` parameters, a [mutable block](#local-mutation) is the one place a variable is written in place, and an [existential type](#existential-type) hides the representation of parts with different state. The table below gives the tool for each need.

| Need | Moxie's tool | Mutability |
| --- | --- | --- |
| Enforce a rule about a value | Opaque type with `export`ed functions | Immutable |
| Hide a private counter or handle | A closure over an `Atom`, or a tuple field | Only the `Atom` |
| Thread state through a pipeline | `ref` parameters, returned tuples | Immutable |
| An in-place algorithm | A `mutable` block | Local only, never visible |
| Parts with different hidden state | `any Interface` | Immutable |

See *[Naming types: aliases, opaque types, and unions](learn/18-types-of-types.html)* and *[In-place algorithms: `mutable` blocks](learn/56-mutable-blocks.html)*.

### Opaque type {#opaque-type}

An opaque type is the module-level answer to a class with private fields. Other packages can name the type and hold it, but they can't construct or inspect it, so the only way to get the type is through the functions that check its rules. A "change" is always a new value made by a function you wrote. See *[Naming types: aliases, opaque types, and unions](learn/18-types-of-types.html)*.

### State {#state}

A program carries changing state in two ways that keep every value immutable. A `ref` parameter carries state through a call: the callee gets a copy, rebinds it, and the final value goes back to the caller's variable. Returning the state with the answer, as a tuple, does the same explicitly. See *[State, lenses, lazy sequences, and monoids](learn/39-state-lenses-monoids.html)*.

### Atom {#atom}

An `Atom` holds an immutable value and swaps in a new one, lock-free, through a pure function, as in `swap(counter, _ + 1)`. Readers always get an immutable snapshot. The `Atom` is the only mutable state that is shared or outlives a call, so a closure that captures one is where state lasts past a single call. See *[Atoms and futures](learn/24-atoms-and-futures.html)*.

### Lens {#lens}

A path that names a spot inside nested tuples, such as `/User/firm/name`. A lens is an ordinary function, so you can store it, pass it and compose it. Moxie gives you `replace` and `modify` for it, and you never write the nested-copy boilerplate. See *[State, lenses, lazy sequences, and monoids](learn/39-state-lenses-monoids.html)*.

### Ownership and moves {#ownership}

A resource, such as a channel end, a timer, a file or a database connection, is a handle with an identity. It is moved, with one owner at a time, rather than copied, and a tuple that holds a resource is a resource too. See *[Fibers and channels](learn/22-fibers-and-channels.html)*.

### Local mutation {#local-mutation}

Inside a `mutable` block you can write to your own variables in place, and nothing outside can tell. The function around the block stays pure. Inside the block, `=` declares a variable the first time and assigns to it after that, and `x += e`, `out(i) = v` and `p.f = e` write in place with no rebinding. Values enter the block by copy, or by move when the old one is dead, and leave as ordinary immutable values. The block is an expression, and its last line is the value. Haskell needs the `ST` monad and a rank-2 type for the same guarantee. See *[In-place algorithms: `mutable` blocks](learn/56-mutable-blocks.html)*.

## 5. Monads and abstractions

These are the names for ways of working with a value inside a container. You don't need them to use `map`, `?` or `|>>`, but they matter when you write code that works for every container, or give your own type the same abilities. See *[Functors and monads](learn/37-functors-and-monads.html)*.

### Functor {#functor}

An interface with `fmap`, which changes the value inside a container with a plain function. `<$>` is the operator for it. The prelude gives instances for `Result`, `Stream`, `List` and `Array`, and you can write one for your own type. See *[Functors and monads](learn/37-functors-and-monads.html)*.

### Applicative {#applicative}

An interface for combining several containers. `<*>` applies a function held in a container to a value in another, so independent inputs combine, with the first failure winning. See *[Functors and monads](learn/37-functors-and-monads.html)*.

### Monad {#monad}

An interface with `pure` and `flat_map`, for chaining steps where each produces a new container. `pure` puts a value into the container, and `flat_map` runs the next step on the value inside. The prelude gives instances for `Result`, `Stream`, `List` and `Array`. Types such as `Maybe`, `Option`, `Either`, `State` and parser types are not built into the language or its library: you define the type and write its `impl Monad[...]`, and then `|>>`, `<$>`, `<*>` and `for` work on it. See *[Functors and monads](learn/37-functors-and-monads.html)*.

### Bind {#bind}

The operator `|>>` runs the next step on the value inside a container and stops at the first failure. It is the right choice when each step needs only the result of the one before it, and it works with any type that has a `Monad` impl. See *[Functors and monads](learn/37-functors-and-monads.html)*.

### Traverse {#traverse}

Applies a function that can fail to every element of a collection. `traverse` stops at the first failure, which is right for a pipeline. `validate` runs the function on every element and gathers the errors, which is right for a form. `par_traverse` is `traverse` for a function that gives a `Result`, run in parallel with a limit. See *[Errors in larger programs](learn/26-errors-in-larger-programs.html)*.

### Sequence {#sequence}

Turns a list of `Result`s into a `Result` of a list, stopping at the first `Err`. `traverse(f, xs)` is `sequence` of `map(f)`. See [Traverse](#traverse).

### Semigroup {#semigroup}

A type with an associative way to combine two values, `combine`. `String` and `List[T]` combine with `+`. A number has more than one way to combine, so you pick one by wrapping it, for example `Sum` or `Min`. See *[State, lenses, lazy sequences, and monoids](learn/39-state-lenses-monoids.html)*.

### Monoid {#monoid}

A semigroup that also has an identity value, `empty`, such as `""` for text or `List()` for lists. `fold_all` combines a list of monoid values, and `fold_map` maps each item to a monoid value first. See [Semigroup](#semigroup) and *[State, lenses, lazy sequences, and monoids](learn/39-state-lenses-monoids.html)*.

### Monad transformer {#monad-transformer}

Stacks two effects into one monad, such as state over failure. Transformers need closures of one type per signature, so they ship only with moxie/gc, as the library `fp.trans`. In GC-free moxie, handle several effects with `Result` and `?` for failure, a tuple threaded through a `reduce` for state, and a `mutable` block for in-place updates. See *[Transformers and the mtl classes](learn/63-transformers.html)*.

### State monad {#state-monad}

A monad that threads state through a computation. *(moxie/gc)* The standard package `fp.state` provides it. In GC-free moxie, the state monad is written as a `ref` parameter or a returned tuple (see [State](#state)). See *[State, lenses, lazy sequences, and monoids](learn/39-state-lenses-monoids.html)*.

### Reader and writer {#reader-writer}

A reader passes a read-only setting to every step, and a writer collects a log alongside a result. *(moxie/gc)* These are monads in the garbage-collected dialect. In GC-free moxie, pass the setting as a parameter, or return a tuple `(value, log)`. See *[Reader, writer, and continuations](learn/62-reader-writer-continuations.html)*.

### Continuation {#continuation}

A continuation lets a computation jump out early. *(moxie/gc)* Continuation monads ship only with the garbage-collected dialect. In GC-free moxie, use `break(value)` in a loop, a `?` that returns an `Err`, or a `when` that returns early. See *[Reader, writer, and continuations](learn/62-reader-writer-continuations.html)*.

### Free monad {#free-monad}

A program described as data: a command, plus what to do with its answer. A separate handler decides what the commands actually do, so the same program can talk to the real world in production and to a script in a test. The standard package `fp.freer` provides the freer form, which needs no `Functor` for the commands. See *[Programs with effects as data: the freer monad](learn/42-freer-monad.html)*.

### GADT {#gadt}

A generalized algebraic data type: an enum whose cases each state their own result type after their parameters. Such an enum can describe a typed evaluator, where each case knows the type it produces. See *[GADTs and typestate](learn/43-gadts-and-typestate.html)*.

### Tagless final {#tagless-final}

Writes a language as an interface, so a program is a generic function that builds its result through that interface. Each `impl` is an interpreter, and you can add operations and interpreters without touching each other. Unlike a data type, the program is a function, so you can't look inside it. See *[Tagless final: one program, many interpreters](learn/40-tagless-final.html)*.

### Expression problem {#expression-problem}

The difficulty that a new operation is easy to add to a data type, while a new variant means editing the type and every function over it. Tagless final and open data types are two ways out, and the second keeps real data you can inspect, rewrite and serialize. See *[Data types that grow: the expression problem](learn/41-open-data-types.html)*.

## 6. Limits {#limits}

Some functional patterns don't fit in moxie, or fit only with conditions. These are the ones to know.

- **There is no IO monad.** Effects are inferred from what a function does, and `pure fn` lets you ask the compiler to enforce purity.
- **Closures and storage.** A closure's size depends on what it captures, so a capturing closure can live in a `Dict`, a tuple field or a channel only with others that capture the same kinds of values. The type says so with `with`, as in `(Int) -> Int with (Int)`. A function returns exactly one closure type. Plain functions can be stored: a lambda that uses only constants, or names bound once to values known at compile time, counts as plain. Closures can always be passed, returned and composed.
- **In the GC-free dialect, a closure can't live in a tuple field.** A closure that captures values in a tuple field would leave the captured values with no owner. The record-of-functions style is written with an interface and a tuple that holds its state, as in [Modularity](#modularity). The `moxie/gc` dialect does allow the record-of-closures style. See *[The two dialects](learn/60-the-two-dialects.html)*.
- **A State monad can be defined only as a local value** in GC-free moxie, with no loops or recursion over runtime-length data. `ref` threading is the recommended way to carry state.
- **Type constructors take at most one hole,** as in `Result[_, E]`. Type lambdas fix any argument.
- **Evaluation is eager,** apart from `lazy` parameters and streams, and nothing is memoized for you.
- **The compiler doesn't check the monad laws.** It checks types and purity, but it doesn't prove that a monad you write obeys them.
