---
layout: default
toc: true
terms: true
dialect: gc
title: "dbg · moxie/gc function"
---

# `dbg`

<p class="specref"><a href="../reference.html#fn-dbg">The alphabetical list</a> · <a href="../spec.html#s22">Spec §22</a></p>

## Signature {#signature}

```
fn dbg[T](x T) T
```

## Description {#description}

Prints a value, with the line it is on, to the error stream, and returns it unchanged, so you can drop it into the middle of an expression to see what is going on. It is allowed anywhere, whatever the effects of the surrounding code.

**Parameters**

- `x`: any value.

**Returns** `x`.

## Effects {#effects}

**Effect:** prints, but is allowed in any code

## Examples {#examples}

```
> dbg(2 + 3) * 10
50
```

