---
layout: default
toc: true
terms: true
title: "run_command · moxie function"
---

# `run_command`

<p class="specref"><a href="../reference.html#fn-run_command">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn run_command(program String) Result[Output, Error]
fn run_command(program String, args List[String]) Result[Output, Error]
```

## Description {#description}

Runs a program, waits for it to end, and gathers what it printed.

**Parameters**

- `program`: the program to run.
- `args` (optional): a `List[String]` of arguments.

**Returns** `Ok(Output)` with the exit code and the text of its standard output and error, or `Err` if it can't be started.

## Effects {#effects}

**Effect:** parks

**Needs permission:** process

## Examples {#examples}

```
> run_command("echo", List("hi")) |> map_ok((o) -> o.stdout)
Ok("hi\n")
```

