---
layout: default
toc: true
terms: true
dialect: gc
title: "read_all · moxie/gc function"
---

# `read_all`

<p class="specref"><a href="../reference.html#fn-read_all">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn read_all() Result[String, Error]
fn read_all(src Io) Result[String, Error]
```

## Description {#description}

Reads everything that is left of the input, as one `String`.

**Parameters**

- `src` (optional): an `Io`; the default is standard input.

**Returns** `Ok(text)`, or `Err`.

## Effects {#effects}

**Effect:** parks

**Needs permission:** stdin

## Examples {#examples}

```
> fn everything() Result[String, Error]
  read_all()
println(with_stdin("one\ntwo\n", everything))
Ok("one\ntwo\n")
```

