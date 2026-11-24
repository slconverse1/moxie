---
layout: default
dialect: gc
title: "Help"
---
# HELP

How to find your way around this site (moxie/gc, the dialect with a garbage collector).

## The tabs

- **moxie/gc**: the introduction.
- **Mixer’s Guide**: lessons, in order, from the first program on. Each lesson ends with links into the Spec.
- **Spec**: the language specification, and under it the reference, with a page for every function.
- **Tutorial**: a shorter walk through the language.
- **Style**: how moxie code is laid out and named.
- **Try moxie/gc**: write and run a program in your browser.
- **REPL**: type one line at a time and see its value and type.
- **Source**: the project on GitHub, with the interpreter and the tests.

## Moving back and forth

The site keeps its own history of the Introduction, Guide, Spec and reference pages you open, separately from the other dialect’s. Typed addresses, bookmarks and the Tutorial, Style, Try and REPL pages are not part of it.

- **Left and right arrow keys** step one page back or forward. Hold a key and the pages flow by until you let go.
- **A swipe** (on a touch screen) moves through up to ten pages at a pace you can follow. Swipe again and it runs through the pages it was already showing, then ten more.
- **Tap, click or press any key** while pages are moving to stop on the page in view. That page opens in full and becomes the current page.

## Try and REPL

**Try moxie/gc** has a program you can edit and run; the output appears below it. The **REPL** takes one expression or declaration at a time and keeps the results as `$res1`, `$res2`, and so on. In the REPL, `:help` lists its commands, `:type expr` gives the type of an expression without running it, `:results` lists every result, and `:reset` forgets the session. Both run in your browser, so the first visit downloads the interpreter (about 10 MB).

## Looking things up

Names in code samples, such as function names, types and keywords, link to their reference entries. Every function has its own page, with its signature, what it does and an example you can run. In the moxie/gc Spec a red line in the right margin marks a rule that applies only to this dialect.

## Running moxie on your own computer

Get the interpreter and the tests from **Source**, then:

    python3 -m moxie run examples/gradebook.mxi
    python3 -m moxie test examples/gradebook.mxi
