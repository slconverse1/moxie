---
layout: default
toc: true
terms: true
title: "with_timeout · moxie function"
---

# `with_timeout`

<p class="specref"><a href="../reference.html#fn-with_timeout">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn with_timeout[T](d Duration, f (Cancel) -> Result[T, Error]) Result[T, Error]
```

## Description {#description}

Runs a function but gives up after a time limit. The function receives a `Cancel` that is triggered when time runs out.

**Parameters**

- `d`: the time limit.
- `f`: a function from a `Cancel` to a `Result`.

**Returns** the function's `Result`, or `Err` with code `TIMED_OUT` if time ran out first.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> with_timeout(500ms, (c) -> Ok(1))
Ok(1)
```

```
> fn slow(c Cancel) Result[Int, Error]
  sleep(300ms)
  Ok(1)
println(with_timeout(20ms, slow))
Err(Error(code: 12, message: "with_timeout: timed out"))
```

