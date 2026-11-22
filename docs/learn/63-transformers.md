---
layout: default
learn: true
title: "Transformers and the mtl classes · Mixer’s Guide moxie"
---
<p class='eyebrow'>Functional programming</p>

# 54. Transformers and the mtl classes

<div class='specref' markdown='1'>In the Spec: [23. Functional programming support](../spec.html#s23)</div>

Monad transformers need closures of one type per signature, so they ship only with moxie/gc. In GC-free moxie, handle several effects at once with the tools in earlier lessons: `Result` and `?` for failure, a tuple threaded through a `reduce` for state, and a `mutable` block (lesson 19) for the places where in-place updates are the clearest code.

---

[← Reader, writer, and continuations](62-reader-writer-continuations.html) · [Contents](./) · [Receiver blocks, interface composition, and mocks →](45-receiver-blocks-and-mocks.html)
