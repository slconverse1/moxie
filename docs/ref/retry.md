---
layout: default
toc: true
terms: true
title: "retry · moxie function"
---

# `retry`

<p class="specref"><a href="../reference.html#fn-retry">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn retry[T](n Int, delay Duration, f () -> Result[T, Error]) Result[T, Error]
```

## Description {#description}

Calls a function that can fail, again and again until it succeeds or `n` tries have been used, waiting between tries.

**Parameters**

- `n`: the most tries to make.
- `delay`: the wait between tries.
- `f`: a function with no arguments that returns a `Result`.

**Returns** the first `Ok`, or the last `Err`.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> retry(3, 1ms, () -> Ok("ok"))
Ok("ok")
```

