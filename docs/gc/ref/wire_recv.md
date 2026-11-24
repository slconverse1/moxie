---
layout: default
toc: true
terms: true
dialect: gc
title: "wire_recv · moxie/gc function"
---

# `wire_recv`

<p class="specref"><a href="../reference.html#fn-wire_recv">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn wire_recv[T](w Wire) Result[T, Error]
```

## Description {#description}

Waits for a value from a `Wire`. The type you expect is written in brackets; it must be the type that was sent.

**Parameters**

- `T` (in brackets): the type expected.
- `w`: a `Wire`.

**Returns** `Ok(value)`, or `Err` if the wire is closed.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> (a, b) = wire_pair()
wire_send(a, 5)
println(wire_recv[Int](b))
Ok(5)
```

