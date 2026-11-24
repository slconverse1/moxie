---
layout: default
toc: true
terms: true
dialect: gc
title: "send_to · moxie/gc function"
---

# `send_to`

<p class="specref"><a href="../reference.html#fn-send_to">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn send_to(u Udp, host String, port Int, data String) Result[Unit, Error]
fn send_to(u Udp, host String, port Int, data Array[Byte]) Result[Unit, Error]
```

## Description {#description}

Sends one UDP packet.

**Parameters**

- `u`: a `Udp`.
- `host`, `port`: where to send it.
- `data`: a `String` or an `Array[Byte]`.

**Returns** `Ok(())`, or `Err`. Success doesn't mean the packet arrived: UDP doesn't promise that.

## Effects {#effects}

**Effect:** parks

**Needs permission:** net

## Examples {#examples}

```
> a = bind_udp(0) |> unwrap()
b = bind_udp(0) |> unwrap()
println(send_to(a, "127.0.0.1", port_of(b), "ping"))
close(a)
close(b)
Ok(())
```

