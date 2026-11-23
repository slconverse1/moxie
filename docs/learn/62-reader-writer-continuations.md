---
layout: default
learn: true
title: "Reader, writer, and continuations · Moxie Mixer’s Guide"
---
# 53. Reader, writer, and continuations

<div class='specref' markdown='1'>In the Spec: [23. Functional programming support](../spec.html#s23)</div>

The monads in this lesson and the next are packages that need closures of one type per signature, which GC-free moxie does not have, so they ship only with moxie/gc. The idea of each, and what to use instead, is below.

- **Reader** passes a read-only setting to every step. In GC-free moxie, pass the setting as a parameter, or use a receiver block (lesson 55).
- **Writer** collects a log alongside a result. Return a tuple `(value, log)`, or build the log with a `reduce`.
- **Continuations** let a computation jump out early. Use `break(value)` in a loop, a `?` that returns an `Err`, or a `when` that returns early.

Lesson 46 and lesson 49 cover the monads that do exist in GC-free moxie.

---

[← GADTs and typestate](43-gadts-and-typestate.html) · [Contents](./) · [Transformers and the mtl classes →](63-transformers.html)
