---
layout: default
toc: true
terms: true
title: "println · moxie function"
---

# `println`

<p class="specref"><a href="../reference.html#fn-println">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn println() Unit
fn println[T](x T) Unit
fn println[T](out Io, x T) Unit
```

## Description {#description}

Writes a value followed by a line end. The value is shown as text the way `show` would, except that a `String` is written without its quotes. With no argument it writes an empty line. With an `Io` first, it writes there, for instance to a network connection.

**Parameters**

- `out` (optional): an `Io` to write to; the default is standard output.
- `x` (optional): the value.

**Returns** nothing.

## Effects {#effects}

**Effect:** prints

## Examples {#examples}

```
> println("hello")

hello
```

```
> println(42)

42
```

```
> println(List(1, 2))
println()
println("after a blank line")

List(1, 2)

after a blank line
```

