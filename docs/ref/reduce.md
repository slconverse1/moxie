---
layout: default
toc: true
terms: true
title: "reduce · moxie function"
---

# `reduce`

<p class="specref"><a href="../reference.html#fn-reduce">The alphabetical list</a> · <a href="../spec.html#s13">Spec §13</a></p>

## Signature {#signature}

```
fn reduce[T, A](init A, f (A, T) -> A, xs Seq[T]) A
```

## Description {#description}

Folds the items into one value. It starts from `init` and calls `f(acc, item)` for each item in turn, passing each result on as the next `acc`. An empty source gives `init` back.

**Parameters**

- `init`: the starting value.
- `f`: a function of the running value and the next item, giving the new running value.
- `xs`: the items.

**Returns** the final value, of the same type as `init`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> List(1, 2, 3) |> reduce(0, (acc, x) -> acc + x)
6
```

```
> List() |> reduce(7, (acc, x) -> acc + x)
7
```

```
> List("a", "b", "c") |> reduce("", (acc, s) -> acc + s)
"abc"
```

