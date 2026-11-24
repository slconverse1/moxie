---
layout: default
toc: true
terms: true
title: "connect · moxie function"
---

# `connect`

<p class="specref"><a href="../reference.html#fn-connect">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn connect(host String, port Int) Result[Io, Error]
```

## Description {#description}

Opens a TCP connection to a host and port. The name is looked up, which is why this can take a while and why other fibers run meanwhile.

**Parameters**

- `host`: a name or address.
- `port`: the port number.

**Returns** `Ok(Io)`, or `Err` if the connection fails.

## Effects {#effects}

**Effect:** parks

**Needs permission:** net

## Examples {#examples}

```
> l = listen(0) |> unwrap()
c = connect("127.0.0.1", port_of(l)) |> unwrap()
println(is_ok(write_bytes(c, Array(1))))
close(c)
close(l)
true
```

