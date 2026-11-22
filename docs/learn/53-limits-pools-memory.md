---
layout: default
title: "Limits, pools, and the memory budget · Learn moxie"
---
<p><small>Quality and larger programs</small></p>

# 34. Limits, pools, and the memory budget

A moxie program has no garbage collector, so the compiler works out ahead of time how much of each counted resource it can have: channels, timers, atoms, files and sockets, listeners, and the fibers themselves. This lesson shows how to read those counts, how to set limits on them, and how to give a program a memory budget.


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

## Reading the counts

`moxie pools FILE` prints the counts, and `--header OUT` writes them as the **pool header**, a small JSON file:

```
$ moxie pools main.mxi --header pools.json
$ moxie --header=pools.json run main.mxi
```

`moxie --pools run FILE` prints the most of each resource that were open at once, so you can compare the compiler's upper bound with what the program did.

Running with `--header` (or naming the file in the manifest, `[pools]` `header = "pools.json"`) checks that the header was made for this program, and refuses to start if it wasn't. The check uses a hash of the tokens of the file and of the packages it imports, so reformatting with `moxie fmt` or editing a comment doesn't matter, but changing a package does.

The program is then held to the header's numbers: a pool that would go over its count, or one more fiber than the header allows, aborts with a message that names the pool. For a correct program that never happens, because the counts are an upper bound; if it does, the tally has a bug.

## A memory budget

The manifest can also set a memory budget:

```moxie
[fibers]
memory = "64KiB"
stack = "16KiB"

[program]
memory = "1MiB"
```

Each fiber needs its `memory` plus its `stack`, and the program needs that for the largest number of fibers it can have. It also needs room for the pools. The start is refused when `[program] memory` is too small, with the sum in the message.

A pool costs a fixed amount for its kind plus the size of what it holds (a channel's capacity times its element), and `moxie pools` prints the total. The size of the element or value must be known, so write `Chan[String[32]][4]()` rather than a channel of a plain `String`, and `Atom[Point](p)` rather than an `Atom` of a value that isn't a number.

A budget needs every fiber function to have a limit, since a count that is unknown can't be checked, and it needs both `memory` and `stack`. Sizes are `"64KiB"` (1024-based), `"64KB"` (1000-based), or a plain number of bytes.

A fiber's `memory` is two stacks in one: `strings` for the text it builds as it runs and `temps` for the lists and copies its pipelines make. Give them separately, `strings = "24KiB"` and `temps = "40KiB"`, when you know the split, or write `memory` alone, or `memory` with one of the two and the other is the rest. A fiber that fills one of them aborts even if the other has room. The budget adds the two, and its message shows both.

Mistakes: keeping an old header after changing the program (it is refused as stale), and setting a budget while a fiber function has no `fiber[n]`.

## What to remember

- `fiber[n]` limits how many copies of a fiber run at once; `go` waits for a slot, `try_go` gives `Err(NO_SLOT)`.
- `moxie pools` shows the counts; a pool header pins them for a build.
- A memory budget in `Moxie.toml` needs a limit on every fiber function and a known size for every pool element.

---

[← Errors in larger programs](26-errors-in-larger-programs.html) · [Contents](./) · [Packages and imports →](27-packages.html)
