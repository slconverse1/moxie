---
layout: default
title: "FP Overview · Moxie"
---
# FP Overview

This page explains the functional ideas that moxie is built on, in general terms, and then says how moxie does each one. Every section links to the Mixer's Guide lessons that show it in code. Sections 1 to 3 are drafted here; the rest follows after review.

## 1.1 Values and functions

**a. Values, not variables.** A value never changes once it exists. Writing `x = 5` states that `x` is 5 from then on, as in a proof. A new value gets a new name. See *[Values and names](learn/03-values-and-names.html)* and *[Lists](learn/15-lists.html)*.

**b. Expressions, not statements.** Most things produce a value: an `if`, a `when`, a block. You combine values into bigger values instead of changing them step by step. See *[Truth and choices](learn/06-truth-and-choices.html)*.

**c. Functions as values.** A function can be stored, passed and returned like any other value. A function that takes or returns a function is called higher-order. See *[Functions](learn/08-functions.html)* and *[Anonymous functions and closures](learn/09-lambdas-and-closures.html)*.

**d. Closures.** A function can remember the names around it where it was written. That captured data travels with the function. See *[Anonymous functions and closures](learn/09-lambdas-and-closures.html)*.

**e. Pattern matching.** Instead of a chain of `if`s that test a value's shape, you write one case per shape and the compiler checks that the cases cover them all. See *[Patterns](learn/19-patterns.html)* and *[Binary patterns and type tags](learn/51-binary-patterns-and-type-tags.html)*.

**f. Recursion, tail calls and loops.** Without changing variables, a loop becomes a function that calls itself. A call in tail position, where nothing is left to do after it returns, can reuse the same stack space, so the recursion can run as long as it needs. Moxie makes a tail call reuse the frame, and `tailrec` makes the compiler check that a recursion really is a tail call. A loop and a tail-recursive function are two ways of writing the same thing. See *[Recursion and function clauses](learn/10-recursion-and-clauses.html)* and *[Loops](learn/07-loops.html)*.

## 1.2 Values and functions (advanced)

**a. map, filter and fold.** These three replace most explicit loops over a collection. `map` transforms each element, `filter` keeps some, and `fold` (called `reduce` in moxie) combines them into one value. See *[Lists](learn/15-lists.html)* and *[Pipelines and streams](learn/21-streams-and-pipelines.html)*.

**b. Composition and pipelines.** Composition joins two functions into one. Moxie's operators for this, which you will see in the lessons:

- `~>` is forward composition: `f ~> g` means "apply `f`, then `g`."
- `|>` is the pipe: `xs |> f()` passes `xs` into `f` as its first argument.
- `|>>` is bind, `<$>` maps a plain function over a value in a container, and `<*>` applies a function held in a container to a value in one.
- `&` and `_` are placeholders: `_` marks where a value goes in a call, so `map(double, _)` is a function that waits for its list.

Because `~>` applies stages in the order written, backward composition is written by reversing the stages. For mathematical order, `compose` takes any number of functions and applies the last one first: `compose(f, g, h)(x)` is `f(g(h(x)))`. A chain of functions passed to `compose` must all take and return the same type. See *[Values, purity, and composing functions](learn/36-purity-and-composition.html)* and *[Pipe slots and caching](learn/50-pipe-slots-and-caching.html)*.

**c. Purity and effects.** A pure function returns the same result for the same arguments and does nothing else. Effects such as printing or reading a file are visible in the type, and `pure fn` asks the compiler to check that a function has none. See *[Values, purity, and composing functions](learn/36-purity-and-composition.html)*.

**d. Laziness and evaluation order.** Most arguments are computed before a call. A stream computes its elements only when they are needed, so a long pipeline does only the work its consumer asks for. See *[Pipelines and streams](learn/21-streams-and-pipelines.html)*.

## 2. Data and missing values

**a. Enums and variants.** An enum is a value that is one of several named cases, and each case can hold its own data. A `when` over an enum must cover every case. See *[Enums](learn/13-enums.html)*.

**b. Tuples as records.** A tuple groups named fields into one value, and fields can be read by name or position. Tuples are the usual way to bundle data. See *[Tuples](learn/12-tuples.html)*.

**c. Missing and failed values.** Moxie has no `null`. A value that may be absent is an `Option`, and an operation that may fail returns a `Result`, which the compiler makes you handle. See *[Missing values and failures: Option and Result](learn/14-missing-and-failed.html)*.

## 3. Structure

**a. Modularity and information hiding.** A program is built from parts that keep their insides private and show the rest of the program a small interface, so one part can be replaced without changing the others. See *[Packages and imports](learn/27-packages.html)* and *[Methods and interfaces](learn/20-interfaces.html)*.

**b. Encapsulation without objects.** An object keeps its data private and changes it only through its methods. Functional languages get the same protection from other tools: opaque types that hide a value's representation, closures that hide their captured data, and `mutable` blocks whose changes can't leak out. See *[Naming types: aliases, opaque types, and unions](learn/18-types-of-types.html)* and *[In-place algorithms: `mutable` blocks](learn/56-mutable-blocks.html)*.

**c. Interfaces as clubs, and typeclasses.** An interface is a set of operations, and a type joins it by writing an `impl`. A type can join many interfaces, and joining adds nothing to the type itself. There is no inheritance. A generic function can require membership in an interface, and any member can be used. See *[Methods and interfaces](learn/20-interfaces.html)* and *[Typeclasses](learn/46-typeclasses.html)*.

**d. Generics.** A generic function is written once for many types. The compiler checks each use at the type it is given. See *[Generic functions](learn/11-generics.html)*.

**e. State without mutation.** A program can carry changing state by passing a new value from one step to the next, or by using an `Atom`, which swaps in a new immutable value without locks. Lenses let you read and update a field deep inside a value. See *[State, lenses, lazy sequences, and monoids](learn/39-state-lenses-monoids.html)* and *[Atoms and futures](learn/24-atoms-and-futures.html)*.
