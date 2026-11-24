---
layout: default
toc: true
terms: true
dialect: gc
title: "close · moxie/gc function"
---

# `close`

<p class="specref"><a href="../reference.html#fn-close">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn close[T](x T) Unit
```

## Description {#description}

Closes a channel or a resource. Readers get what is already buffered and then `Err` with code `CLOSED`; further writes fail. Closing twice is harmless.

**Parameters**

- `x`: a channel end, or something that holds a resource such as a connection, listener or `Wire`.

**Returns** nothing.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> (r, w) = Chan[Int][2]()
write(w, 5)
close(w)
println(read(r))
println(read(r))
Ok(5)
Err(Error(code: 1, message: "channel closed"))
```

