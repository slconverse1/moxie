---
layout: default
toc: true
terms: true
title: "race · moxie function"
---

# `race`

<p class="specref"><a href="../reference.html#fn-race">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn race[T](f (Cancel) -> T, g (Cancel) -> T) T
```

## Description {#description}

Runs two functions at the same time and returns the answer of whichever finishes first. The loser is cancelled through its `Cancel`, so it should check it, and its result is thrown away.

**Parameters**

- `f`, `g`: functions that take a `Cancel` and return a value of one type.

**Returns** the value of the winner.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> fn slow(c Cancel) Int
  sleep(500ms)
  2
println(race((c) -> 1, slow))
1
```

