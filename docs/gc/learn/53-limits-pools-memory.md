---
layout: default
dialect: gc
learn: true
title: "Limits, pools, and the memory budget · Mixer’s Guide moxie/gc"
---
<p><small>Quality and larger programs</small></p>

# 35. Limits, pools, and the memory budget


In moxie/gc the runtime manages memory for you, so pools and budgets are not part of the language. A fiber function can still say how many copies may run at once with `fiber[n]`, which this lesson starts with, but the pool header and the memory budget described later apply only to GC-free moxie.

## How many fibers at once

A fiber function says how many copies may run at once with `fiber[n]`. The manifest can give a default with `[fibers] limit`. `go` waits for a free slot when all of them are alive, and `try_go` returns `Err(NO_SLOT)` instead:

```moxie
fiber[2] fn w(tx ChanW[Int]) Unit
  \write(tx, 2)

rx, tx = Chan[Int][1]()
go w(tx)
println(read(rx)?)
```
**Output:**

```
2
```


## What to remember

- `fiber[n]` limits how many copies of a fiber run at once; `go` waits for a slot, `try_go` gives `Err(NO_SLOT)`.

*In the Spec: [3a. The Moxie runtime](../spec.html#s3a), [19. Resources, pools, packages](../spec.html#s19)*

---

[← Errors in larger programs](26-errors-in-larger-programs.html) · [Contents](./) · [Packages and imports →](27-packages.html)
