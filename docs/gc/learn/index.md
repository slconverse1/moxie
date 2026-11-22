---
layout: default
dialect: gc
title: "Learn moxie/gc"
---
# LEARN MOXIE/GC

This is a course in moxie/gc, taught one lesson at a time. Each lesson explains one idea, shows it in small programs, and shows exactly what those programs print. Every example is complete, so you can copy any of them into a file and run it, and every output was produced by running the example on the reference interpreter.

The course has no exercises. It has examples, many of them, and it tries to say what the language does and why. Moxie is a *design language*: a written specification and a working reference interpreter, not yet a compiler that produces native programs. So what you learn here is the language as designed, and what you run is the interpreter that implements it.

You don't need to know any functional programming. If you do, the lessons point out where moxie differs from what you might expect. For the exact rules, the [Spec](../spec.html) is the reference, and the [Tutorial](../tutorial.html) builds one larger program from start to finish.


## Getting started

1. [Running moxie](01-run.html)
2. [Your first program](02-first-program.html)
3. [Values and names](03-values-and-names.html)
4. [Numbers](04-numbers.html)
5. [Text](05-text.html)
6. [Truth and choices](06-truth-and-choices.html)
7. [Loops](07-loops.html)

## Functions

8. [Functions](08-functions.html)
9. [Anonymous functions and closures](09-lambdas-and-closures.html)
10. [Recursion and function clauses](10-recursion-and-clauses.html)
11. [Generic functions](11-generics.html)

## Data

12. [Tuples](12-tuples.html)
13. [Enums](13-enums.html)
14. [Missing values and failures: Option and Result](14-missing-and-failed.html)
15. [Lists](15-lists.html)
16. [Arrays and grids](16-arrays.html)
17. [Dicts and sets](17-dicts-and-sets.html)
18. [Naming types: aliases, opaque types, and unions](18-types-of-types.html)
19. [Patterns](19-patterns.html)
20. [Methods and interfaces](20-interfaces.html)

## Streams and pipelines

21. [Streams and pipelines](21-streams-and-pipelines.html)

## Concurrency

22. [Fibers and channels](22-fibers-and-channels.html)
23. [Waiting on several things: select, timers, and cancelling](23-select-timers-cancel.html)
24. [Atoms and futures](24-atoms-and-futures.html)

## Quality and larger programs

25. [Testing, assertions, and checking](25-testing.html)
26. [Errors in larger programs](26-errors-in-larger-programs.html)

## Packages

27. [Packages and imports](27-packages.html)
28. [Input, output, and files](28-input-output-files.html)
29. [Builders: a DSL without macros](29-builders-and-blocks.html)

## Data from outside

30. [JSON and data from outside](30-json.html)
31. [Regular expressions](31-regex.html)
32. [Statistics and prediction](32-statistics.html)
33. [Networking, deadlines, and parallel work](33-networking.html)
34. [Units of measure](34-units.html)
35. [Databases with SQL](35-sql.html)

## Functional programming

36. [Values, purity, and composing functions](36-purity-and-composition.html)
37. [Mapping, sequencing, and combining: functors, applicatives, and monads](37-functors-and-monads.html)
38. [`for` comprehensions](38-for-comprehensions.html)
39. [State, lenses, lazy sequences, and monoids](39-state-lenses-monoids.html)
40. [Tagless final: one program, many interpreters](40-tagless-final.html)
41. [Data types that grow: the expression problem](41-open-data-types.html)
42. [Programs with effects as data: the freer monad](42-freer-monad.html)
43. [GADTs and typestate](43-gadts-and-typestate.html)

## Designing with interfaces

44. [Receiver blocks, interface composition, and mocks](45-receiver-blocks-and-mocks.html)
45. [Typeclasses](46-typeclasses.html)

## Your program and its machine

46. [The system around your program](44-the-system-around-your-program.html)
