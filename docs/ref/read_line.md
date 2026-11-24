---
layout: default
toc: true
terms: true
title: "read_line · moxie function"
---

# `read_line`

<p class="specref"><a href="../reference.html#fn-read_line">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn read_line() Result[String, Error]
fn read_line(src Io) Result[String, Error]
```

## Description {#description}

Reads one line of input, without its line end. It waits, letting other fibers run, until a line arrives.

**Parameters**

- `src` (optional): an `Io` to read from; the default is standard input.

**Returns** `Ok(line)`, or `Err` with code `CLOSED` ("end of input") at the end of the input.

## Effects {#effects}

**Effect:** parks

**Needs permission:** stdin

## Examples {#examples}

```
> fn first() Result[String, Error]
  read_line()
println(with_stdin("one\ntwo\n", first))
Ok("one")
```

```
> fn first() Result[String, Error]
  read_line()
println(is_err(with_stdin("", first)))
true
```

