---
layout: default
dialect: gc
learn: true
title: "Packages and imports · Mixer’s Guide moxie/gc"
---
<p class='eyebrow'>Packages</p>

# 36. Packages and imports

<div class='specref' markdown='1'>In the Spec: [4. Packages, modules, imports, exports, linking](../spec.html#s4)</div>

A program doesn't have to live in one file. Code is split into *packages*, and a package is made of one or more files. This lesson covers how to import code, what a package shares with the rest of the program, and how a larger package is laid out.

## One file as a package

The simplest package is a single file. Here is `util.mxi`, which exports a greeting and a function, and keeps one name to itself:

**`util.mxi`**

```moxie
export greeting String = "hello"
export fn shout(s String) String = upper(s) + "!"
internal retry_limit = 3
```

In the main file, `import util` makes the package's exported names available with the package name in front:

```moxie
import util
println(util.greeting)
println(util.shout("moxie"))
```
**Output:**

```
hello
MOXIE!
```

The import finds `util.mxi` next to the file that imports it.

## What is shared: visibility

A name in a file has one of three levels of visibility:

| Written | Visible to |
|---|---|
| nothing | the same file only |
| `internal` | every file of the same package |
| `export` | everyone who imports the package |

`internal` and `export` start a top-level declaration, and an `export` always has an explicit type. Anything not exported isn't part of the package's interface, so you can change it freely:

**`util.mxi`**

```moxie
export fn shout(s String) String = upper(s) + "!"
fn secret() String = "hidden"
```
```moxie
import util
println(util.secret())
```
**The compiler says:**

```
error: 'secret' in package util is not exported (add `export` to its declaration to use it from another package)
```

## Importing particular names

`import util (shout)` brings just the named functions in, unqualified. `import util as u` renames the package:

**`util.mxi`**

```moxie
export fn shout(s String) String = upper(s) + "!"
export fn whisper(s String) String = lower(s) + "..."
```
```moxie
import util (shout)
import util as u
println(shout("a"))
println(u.whisper("B"))
```
**Output:**

```
A!
b...
```

## Packages of several files

A package of several files has its own folder with a `Moxie.toml` that lists the files in the order they are compiled. The files share the package's `internal` names in that order, and `import shapes` finds the folder:

**`shapes/Moxie.toml`**

```moxie
files = ["base.mxi", "area.mxi"]
```
**`shapes/base.mxi`**

```moxie
export tuple Rect(w Int, h Int)
```
**`shapes/area.mxi`**

```moxie
export fn area(r Rect) Int = r.w * r.h
```
```moxie
import shapes
r = shapes.Rect(3, 4)
println(shapes.area(r))
```
**Output:**

```
12
```

Because `area.mxi` comes after `base.mxi`, it can use `Rect`. The order matters because, as inside one file, a name must be declared before it is used.

A folder with a `main.mxi` (or a `Moxie.toml` that names an `entry`) can be run with just `moxie run`, no file name.

## The standard packages

Some packages ship with the interpreter: `json`, `regex`, `http`, `stats`, `session`, and others. They import the same way, and later lessons use them:

```moxie
import regex
println(regex.is_match(regex.must("^[0-9]+$"), "123"))
println(regex.is_match(regex.must("^[0-9]+$"), "12a"))
```
**Output:**

```
true
false
```

A program's own files win: if you have a `json.mxi` next to your program, `import json` finds yours, not the standard one.

## Everything is linked from source

Moxie programs are linked statically, from source, and code that can never run is pruned. A *link report* lists what each package contributed. There is no separate library to ship and no version of a dependency to go missing at run time.

## Limits and pools

In GC-free moxie the compiler works out ahead of time how many of each counted resource a program can have: channels, timers, atoms, files and sockets, and fibers. `moxie pools file.mxi` prints the counts, and the manifest can set memory budgets (`[fibers] memory`, `[program] memory`). That is covered in the Spec; it is what lets a moxie program say, before it starts, how much memory it will use.

In moxie/gc there is no memory budget to declare: the collector manages memory, so pools and budgets don't apply.

---

[← Limits, pools, and the memory budget](53-limits-pools-memory.html) · [Contents](./) · [Input, output, and files →](28-input-output-files.html)
