---
layout: default
toc: true
terms: true
dialect: gc
title: "wire_pair · moxie/gc function"
---

# `wire_pair`

<p class="specref"><a href="../reference.html#fn-wire_pair">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn wire_pair() (Wire, Wire)
```

## Description {#description}

Makes a connected pair of `Wire`s, ends of a channel that can carry whole values between programs or between a program and a foreign library. What is written to one is read from the other.

**Parameters** none.

**Returns** a pair of `Wire`s.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> (a, b) = wire_pair()
wire_send(a, 5)
println(wire_recv[Int](b))
Ok(5)
```

