---
layout: default
toc: true
terms: true
dialect: gc
title: "listen · moxie/gc function"
---

# `listen`

<p class="specref"><a href="../reference.html#fn-listen">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn listen(port Int) Result[Listener, Error]
```

## Description {#description}

Starts accepting network connections on a port. Port 0 asks the system to pick a free one; `port_of` tells you which.

**Parameters**

- `port`: the TCP port number.

**Returns** `Ok(Listener)`, or `Err` if the port can't be used.

## Effects {#effects}

**Effect:** parks

**Needs permission:** net

## Examples {#examples}

```
> l = listen(0) |> unwrap()
println(port_of(l) > 0)
close(l)
true
```

