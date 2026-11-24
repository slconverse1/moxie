---
layout: default
toc: true
terms: true
dialect: gc
title: "flush · moxie/gc function"
---

# `flush`

<p class="specref"><a href="../reference.html#fn-flush">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn flush() Unit
fn flush(out Io) Unit
```

## Description {#description}

Sends held-back output on its way now, which matters for a prompt that doesn't end in a line end, or before the program does something slow.

**Parameters**

- `out` (optional): an `Io`; the default is standard output.

**Returns** nothing.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> print("a")
flush()
println("b")
ab
```

