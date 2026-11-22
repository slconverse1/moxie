---
layout: default
learn: true
title: "Running moxie · Mixer’s Guide moxie"
---
<p class='eyebrow'>Getting started</p>

# 1. Running moxie

<div class='specref' markdown='1'>In the Spec: [22. Tooling, tests, and checks](../spec.html#s22)</div>

Before any language, you need a way to run programs. There are three, from least to most effort.

**In your browser.** The [Try page](../try.html) runs a program on this site with nothing to install. It is a sandbox: no network, no native libraries, and files that live only in the page. It is the quickest way to try an example from this course.

**With the interpreter.** The reference interpreter is plain Python 3.11 or later, and nothing else. Download [moxie.zip](../moxie.zip), unzip it, and you have a folder named `moxie`. Put a program in a file whose name ends in `.mxi` next to that folder and run it from there. Here is a program, saved as `hello.mxi`:

```moxie
name = "world"
println("Hello, $name!")
```
**Output:**

```
Hello, world!
```

and the command that runs it:

```
$ python3 -m moxie run hello.mxi
Hello, world!
```

**From a clone of the repository.** `git clone https://github.com/slconverse1/moxie` gets you the interpreter, the examples, and the tests. `python3 -m moxie run examples/gradebook.mxi` runs one of the examples.

## The four commands

The interpreter takes a command and a file:

| Command | What it does |
|---|---|
| `python3 -m moxie run hello.mxi` | checks the program, then runs it |
| `python3 -m moxie check hello.mxi` | checks the program and stops: nothing runs |
| `python3 -m moxie test hello.mxi` | runs the program's `test` blocks (lesson on testing) |
| `python3 -m moxie repl` | an interactive session: type an expression, see its value and its type |

"Checks" matters. Moxie finds most mistakes before the program starts: a name that doesn't exist, a number where text was expected, a function called with the wrong arguments. You will see many examples of those compile-time errors in this course, because they are how the language teaches you.

## The REPL

The REPL is the fastest way to explore. Type an expression and it prints the type and the value. The newest result is kept as `$res1`, the one before it as `$res2`, and so on, so the next line can use it. A binding is remembered for the rest of the session:

```
$ python3 -m moxie repl
moxie> 6 * 7
$res1 Int = 42
moxie> $res1 + 1
$res1 Int = 43
moxie> greeting = "hi"
greeting String = "hi"
moxie> "$greeting there"
$res1 String = "hi there"
```

`:help` lists the commands and `:quit` leaves.

## Two dialects

Moxie comes in two dialects. **Moxie** has no garbage collector: values that own something (a file, a socket, a big buffer) are tracked by the compiler, and you move them or close them. **moxie/gc** has a garbage collector and drops those rules. The two are the same language for nearly everything in this course, and the lessons say so when they differ.

This copy of the course is for GC-free moxie, the default. To run the other dialect, add `--gc`: `python3 -m moxie --gc run hello.mxi`. The moxie/gc course is a separate copy of these lessons.

## Windows, macOS, Linux

Unix is the main platform for moxie (macOS, Linux and similar). Check `python3 --version`: if it is older than 3.11, install a current Python from python.org, with `brew install python` on a Mac, or with your system's package manager. Windows has not been tested yet; in principle it should work with `py -m moxie run hello.mxi` from the folder that holds `moxie`.

## An editor

Any text editor works. A [VS Code extension](https://github.com/slconverse1/moxie/tree/main/tools/editor/vscode-moxie) and a [vim syntax file](https://github.com/slconverse1/moxie/tree/main/tools/editor/vim) give colors and 2-space indentation. Indentation matters in moxie: a block is written by indenting its lines two spaces, as you will see in a few lessons.

---

[Contents](./) · [Your first program →](02-first-program.html)
