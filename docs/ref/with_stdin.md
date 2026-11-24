---
layout: default
toc: true
terms: true
title: "with_stdin · moxie function"
---

# `with_stdin`

<p class="specref"><a href="../reference.html#fn-with_stdin">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn with_stdin[T](text String, f () -> T) T
```

## Description {#description}

Runs a function with standard input replaced by some text. It is how a program that reads input is tested without a keyboard.

**Parameters**

- `text`: what the input will contain.
- `f`: the function to run.

**Returns** whatever `f` returns.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> fn first() Result[String, Error]
  read_line()
println(with_stdin("5\n", first))
Ok("5")
```

