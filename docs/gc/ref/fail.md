---
layout: default
toc: true
terms: true
dialect: gc
title: "fail · moxie/gc function"
---

# `fail`

<p class="specref"><a href="../reference.html#fn-fail">The alphabetical list</a> · <a href="../spec.html#s15">Spec §15</a></p>

## Signature {#signature}

```
fn fail[T](code Int) Result[T, Error]
fn fail[T](code Int, message String) Result[T, Error]
```

## Description {#description}

A failed `Result` with an error you make on the spot. The type of the success value is written in brackets.

**Parameters**

- `T` (in brackets): the type the `Result` would have held.
- `code`: an error code.
- `message` (optional): a description.

**Returns** an `Err`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> fail[Int](4, "missing")
Err(Error(code: 4, message: "missing"))
```

```
> fail[String](7)
Err(Error(code: 7, message: ""))
```

