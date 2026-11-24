---
layout: default
toc: true
terms: true
dialect: gc
title: "port_of · moxie/gc function"
---

# `port_of`

<p class="specref"><a href="../reference.html#fn-port_of">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn port_of(l Listener) Int
fn port_of(u Udp) Int
```

## Description {#description}

The port a `Listener` or a `Udp` socket is using, which is how you find out the port the system picked when you asked for 0.

**Parameters**

- `l`: a `Listener` or a `Udp`.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> port_of(listen(0) |> unwrap()) > 0
true
```

