---
layout: default
toc: true
terms: true
title: "wire_close · moxie function"
---

# `wire_close`

<p class="specref"><a href="../reference.html#fn-wire_close">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn wire_close(w Wire) Unit
```

## Description {#description}

Closes a `Wire`. The other end can still read what was already sent, and then gets an `Err`.

**Parameters**

- `w`: a `Wire`.

**Returns** nothing.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> (a, b) = wire_pair()
wire_send(a, 1)
wire_close(a)
println(wire_recv[Int](b))
println(is_err(wire_recv[Int](b)))
Ok(1)
true
```

