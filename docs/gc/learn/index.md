---
layout: default
dialect: gc
learn: true
title: "Mixer’s Guide moxie/gc"
---
# MIXER’S GUIDE MOXIE/GC

This is the Mixer’s Guide to moxie/gc, one lesson at a time. (A *mixer* is a programmer who writes moxie.) Each lesson explains one idea, shows it in small programs, and shows exactly what those programs print. Every example is complete, so you can copy any of them into a file and run it, and every output was produced by running the example on the reference interpreter.

The course has no exercises. It has examples, many of them, and it tries to say what the language does and why. Moxie is a *design language*: a written specification and a working reference interpreter, not yet a compiler that produces native programs. So what you learn here is the language as designed, and what you run is the interpreter that implements it.

You don't need to know any functional programming. If you do, the lessons point out where moxie differs from what you might expect. For the exact rules, the [Spec](../spec.html) is the reference, and the [Tutorial](../tutorial.html) builds one larger program from start to finish.


## Getting started

1. [Running moxie](01-run.html)
2. [Your first program](02-first-program.html)
3. [Values and names](03-values-and-names.html)
4. [Moxie for imperative programmers](58-for-imperative-programmers.html)
5. [Numbers](04-numbers.html)
6. [Text](05-text.html)
7. [Templates and locales](59-fmt-and-locales.html)
8. [Truth and choices](06-truth-and-choices.html)
9. [Loops](07-loops.html)

## Functions

10. [Functions](08-functions.html)
11. [Anonymous functions and closures](09-lambdas-and-closures.html)
12. [Recursion and function clauses](10-recursion-and-clauses.html)
13. [Generic functions](11-generics.html)

## Data

14. [Tuples](12-tuples.html)
15. [Enums](13-enums.html)
16. [Missing values and failures: Option and Result](14-missing-and-failed.html)
17. [Lists](15-lists.html)
18. [Arrays and grids](16-arrays.html)
19. [In-place algorithms: `mutable` blocks](56-mutable-blocks.html)
20. [Dicts and sets](17-dicts-and-sets.html)
21. [Naming types: aliases, opaque types, and unions](18-types-of-types.html)
22. [Patterns](19-patterns.html)
23. [Binary patterns, and taking a value apart by its type](51-binary-patterns-and-type-tags.html)
24. [Methods and interfaces](20-interfaces.html)

## Streams and pipelines

25. [Streams and pipelines](21-streams-and-pipelines.html)
26. [More stream tools: sources you build](61-more-stream-tools.html)
27. [Pipe slots, `seq`, and doing work once](50-pipe-slots-and-caching.html)

## Concurrency

28. [Fibers and channels](22-fibers-and-channels.html)
29. [Waiting on several things: select, timers, and cancelling](23-select-timers-cancel.html)
30. [Atoms and futures](24-atoms-and-futures.html)
31. [Session types: a channel that remembers the conversation](52-session-types.html)

## Quality and larger programs

32. [Testing, assertions, and checking](25-testing.html)
33. [Formatting and checking: `moxie fmt` and `moxie check`](57-formatting-and-checking.html)
34. [Errors in larger programs](26-errors-in-larger-programs.html)
35. [Limits, pools, and the memory budget](53-limits-pools-memory.html)

## Packages

36. [Packages and imports](27-packages.html)
37. [Input, output, and files](28-input-output-files.html)
38. [Builders: a DSL without macros](29-builders-and-blocks.html)

## Data from outside

39. [JSON and data from outside](30-json.html)
40. [Regular expressions](31-regex.html)
41. [Statistics and prediction](32-statistics.html)
42. [Networking, deadlines, and parallel work](33-networking.html)
43. [Units of measure](34-units.html)
44. [Databases with SQL](35-sql.html)

## Functional programming

45. [Values, purity, and composing functions](36-purity-and-composition.html)
46. [Mapping, sequencing, and combining: functors, applicatives, and monads](37-functors-and-monads.html)
47. [`for` comprehensions](38-for-comprehensions.html)
48. [State, lenses, lazy sequences, and monoids](39-state-lenses-monoids.html)
49. [Tagless final: one program, many interpreters](40-tagless-final.html)
50. [Data types that grow: the expression problem](41-open-data-types.html)
51. [Programs with effects as data: the freer monad](42-freer-monad.html)
52. [GADTs and typestate](43-gadts-and-typestate.html)
53. [Reader, writer, and continuations](62-reader-writer-continuations.html)
54. [Transformers and the mtl classes](63-transformers.html)

## Designing with interfaces

55. [Receiver blocks, interface composition, and mocks](45-receiver-blocks-and-mocks.html)
56. [Typeclasses](46-typeclasses.html)
57. [Types that compute](47-types-that-compute.html)

## Fields and promises

58. [Properties, field delegates, and proxies](48-properties-delegates-proxies.html)
59. [Refined parameters: proofs in the signature](49-refined-parameters.html)
60. [Contracts: where and invariant](55-contracts.html)

## Your program and its machine

61. [The system around your program](44-the-system-around-your-program.html)
62. [Calling C](54-calling-c.html)
63. [Byte streams: Reader and Writer](65-byte-streams.html)
64. [Moxie and moxie/gc side by side](60-the-two-dialects.html)
65. […moxie: the rest of its toolbox](66-the-rest-of-moxie.html)
66. [Where to go next](64-where-to-go-next.html)
