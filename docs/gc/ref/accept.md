---
layout: default
toc: true
terms: true
dialect: gc
title: "accept · moxie/gc function"
---

# `accept`

<p class="specref"><a href="../reference.html#fn-accept">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn accept(l Listener) Result[Io, Error]
```

## Description {#description}

Waits for the next incoming connection on a `Listener`. Other fibers run while it waits.

**Parameters**

- `l`: a `Listener`.

**Returns** `Ok(Io)` for the new connection, or `Err`.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> accept(l)
Ok(Io())  (when a client connects)
```

