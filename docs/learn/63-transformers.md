---
layout: default
learn: true
title: "Transformers and the mtl classes · Learning Guide moxie"
---
<p><small>Functional programming</small></p>

# 54. Transformers and the mtl classes

Monad transformers need closures of one type per signature, so they ship only with moxie/gc. In GC-free moxie, handle several effects at once with the tools in earlier lessons: `Result` and `?` for failure, a tuple threaded through a `reduce` for state, and a `mutable` block (lesson 19) for the places where in-place updates are the clearest code.

---

[← Reader, writer, and continuations](62-reader-writer-continuations.html) · [Contents](./) · [Receiver blocks, interface composition, and mocks →](45-receiver-blocks-and-mocks.html)
