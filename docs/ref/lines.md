---
layout: default
toc: true
terms: true
title: "lines · moxie function"
---

# `lines`

<p class="specref"><a href="../reference.html#fn-lines">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn lines(src Io) Stream[String]
```

## Description {#description}

The lines of an `Io`, one at a time, until it ends.

**Parameters**

- `src`: an `Io`, such as a connection.

**Returns** a `Stream[String]`.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> for line in lines(conn)
runs once for each line the other side sends
```

