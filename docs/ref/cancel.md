---
layout: default
toc: true
terms: true
title: "cancel · moxie function"
---

# `cancel`

<p class="specref"><a href="../reference.html#fn-cancel">The alphabetical list</a> · <a href="../spec.html#s17">Spec §17</a></p>

## Signature {#signature}

```
fn cancel(c Cancel) Unit
```

## Description {#description}

Asks the work that holds a `Cancel` to stop. Work that is written to check its `Cancel` stops at the next check, and sleeping or waiting inside it is interrupted. Cancelling twice is harmless.

**Parameters**

- `c`: a `Cancel`.

**Returns** nothing.

## Effects {#effects}

**Effect:** uses a resource

## Examples {#examples}

```
> cancel(c)
the work using `c` stops at its next check
```

