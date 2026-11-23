---
layout: default
learn: true
title: "Where to go next · Moxie Mixer’s Guide"
---
# 66. Where to go next

<div class='specref' markdown='1'>In the Spec: [25. Still open](../spec.html#s25), [26. Grammar](../spec.html#s26)</div>

You have now met the whole language, from `println("hello")` to session types and calling C. This last page is a map of the other things on this site and in the repository, and a short list of habits that make moxie programs good ones.

## The rest of the site

- **The Tutorial** builds one small program, a gradebook, a step at a time. It is shorter than this guide and a good first read if you want to see how the pieces fit together before the details.
- **The Spec** is the reference. It defines the language section by section, including the rules this guide only describes: type checking, layout of values, what the compiler must reject, and the standard library. When this guide and the Spec seem to disagree, the Spec wins, and a report that they do is a bug worth filing.
- **The Style guide** says how moxie code should look: names, layout, comments, and when to write a doc comment.
- **Try moxie** and **the REPL** run programs in your browser, with nothing to install. Every example in this guide runs there too, except those that need a network or the file system.
- **The Site Intro** is the long argument for why the language is shaped the way it is. It's the page to send a friend who asks what moxie is for.

## The two dialects

If you read the guide for one dialect and want the other, the same pages exist for both. The differences are in the lesson on the two dialects (lesson 64): collections that grow, persistent updates, one `String` type, closures that go anywhere, and the end of pools and budgets. Reach for GC-free moxie when the worst case must be known before the program runs, and moxie/gc when you want the language without the bookkeeping.

## The interpreter

The reference interpreter in the repository runs everything in this guide. It is a specification you can execute, not a production compiler, so it checks most but not all of what the Spec says, and it is not fast. `INTERPRETER.md` lists what it checks and what it leaves out, and the `examples/` directory has complete programs to read and run:

```
$ python3 -m moxie run examples/gradebook.mxi
$ python3 -m moxie test examples/gradebook.mxi
```

The commands you will use most are `run`, `test`, `check` (parse and type-check without running), `fmt` (canonical layout), `doc` (documentation from `///` comments), and `repl`. Lesson 33 covers `fmt` and `check`, and lesson 32 covers `test`.

## Habits worth keeping

- **Make illegal states unrepresentable.** Reach for an enum or a refined type before a comment that says "never pass zero".
- **Return values; don't mutate.** Update a copy, name the new value, and use a `mutable` block only for a well-bounded stretch of in-place work.
- **Let the compiler argue with you.** Write the type, read the error, and fix the code. The messages say what to add.
- **Test a rule, not just an example.** One `forall` covers hundreds of inputs.
- **Pass resources down; own them in one place.** Channels, files, and connections have one owner at a time, and that makes cleanup automatic.
- **Keep effects at the edge.** A pure core and a thin shell of I/O is easy to test and easy to read.

That is the whole tour. Write something small, run it, and let it grow.

---

[← …moxie: the rest of the moxie toolbox](66-the-rest-of-moxie.html) · [Contents](./)
