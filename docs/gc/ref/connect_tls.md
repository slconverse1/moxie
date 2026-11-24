---
layout: default
toc: true
terms: true
dialect: gc
title: "connect_tls · moxie/gc function"
---

# `connect_tls`

<p class="specref"><a href="../reference.html#fn-connect_tls">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn connect_tls(host String, port Int) Result[Io, Error]
```

## Description {#description}

Like `connect`, but encrypted with TLS. The server's certificate is checked against the system's trusted ones, and a certificate that doesn't match the host name is an `Err`.

**Parameters**

- `host`: a name; it is used to check the certificate.
- `port`: the port.

**Returns** `Ok(Io)`, or `Err`.

## Effects {#effects}

**Effect:** parks

**Needs permission:** net

## Examples {#examples}

```
> connect_tls("example.com", 443)
Ok(Io())
```

