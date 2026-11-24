---
layout: default
toc: true
terms: true
title: "listen_tls · moxie function"
---

# `listen_tls`

<p class="specref"><a href="../reference.html#fn-listen_tls">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn listen_tls(port Int, cert String, key String) Result[Listener, Error]
```

## Description {#description}

Like `listen`, but the connections are encrypted with TLS, using a certificate and key you give.

**Parameters**

- `port`: the TCP port.
- `cert`: the path of the certificate file.
- `key`: the path of the key file.

**Returns** `Ok(Listener)`, or `Err` (for instance if a file can't be read).

## Effects {#effects}

**Effect:** parks

**Needs permission:** net

## Examples {#examples}

```
> listen_tls(8443, "cert.pem", "key.pem")
Ok(Listener())
```

