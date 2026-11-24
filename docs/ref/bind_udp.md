---
layout: default
toc: true
terms: true
title: "bind_udp · moxie function"
---

# `bind_udp`

<p class="specref"><a href="../reference.html#fn-bind_udp">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn bind_udp(port Int) Result[Udp, Error]
```

## Description {#description}

Opens a UDP socket on a port, to send and receive single packets. Port 0 means any free port.

**Parameters**

- `port`: the port.

**Returns** `Ok(Udp)`, or `Err`.

## Effects {#effects}

**Effect:** parks

**Needs permission:** net

## Examples {#examples}

```
> u = bind_udp(0) |> unwrap()
println(port_of(u) > 0)
close(u)
true
```

