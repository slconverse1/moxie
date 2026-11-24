---
layout: default
toc: true
terms: true
dialect: gc
title: "spawn · moxie/gc function"
---

# `spawn`

<p class="specref"><a href="../reference.html#fn-spawn">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn spawn(program String) Result[Child, Error]
fn spawn(program String, args List[String]) Result[Child, Error]
```

## Description {#description}

Starts another program and returns at once, leaving it running. You can then wait for it or stop it.

**Parameters**

- `program`: the program to run.
- `args` (optional): a `List[String]` of arguments.

**Returns** `Ok(Child)`, or `Err` if it can't be started.

## Effects {#effects}

**Effect:** parks

**Needs permission:** process

## Examples {#examples}

```
> spawn("sleep", List("5"))
Ok(Child())
```

