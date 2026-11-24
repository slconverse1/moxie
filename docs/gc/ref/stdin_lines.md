---
layout: default
toc: true
terms: true
dialect: gc
title: "stdin_lines · moxie/gc function"
---

# `stdin_lines`

<p class="specref"><a href="../reference.html#fn-stdin_lines">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn stdin_lines() Stream[String]
```

## Description {#description}

The lines of standard input, one at a time, until the input ends. It is meant for `for` and pipelines.

**Parameters** none.

**Returns** a `Stream[String]`.

## Effects {#effects}

**Effect:** parks

**Needs permission:** stdin

## Examples {#examples}

```
> fn gather() List[String]
  stdin_lines() |> collect()
println(with_stdin("a\nb\nc\n", gather))
List("a", "b", "c")
```

