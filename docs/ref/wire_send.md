---
layout: default
toc: true
terms: true
title: "wire_send · moxie function"
---

# `wire_send`

<p class="specref"><a href="../reference.html#fn-wire_send">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn wire_send[T](w Wire, x T) Result[Unit, Error]
```

## Description {#description}

Sends a value over a `Wire`. The value must be plain data (numbers, text, tuples, lists), not a resource.

**Parameters**

- `w`: a `Wire`.
- `x`: the value.

**Returns** `Ok(())`, or `Err` if the wire is closed.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> (a, b) = wire_pair()
println(wire_send(a, "hi"))
Ok(())
```

