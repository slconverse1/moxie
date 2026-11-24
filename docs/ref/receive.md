---
layout: default
toc: true
terms: true
title: "receive · moxie function"
---

# `receive`

<p class="specref"><a href="../reference.html#fn-receive">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn receive(u Udp) Result[Packet, Error]
```

## Description {#description}

Waits for one UDP packet.

**Parameters**

- `u`: a `Udp`.

**Returns** `Ok(Packet)`, with the data and where it came from, or `Err`.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> receive(u)
Ok(Packet(...))
```

