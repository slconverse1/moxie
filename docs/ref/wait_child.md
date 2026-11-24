---
layout: default
toc: true
terms: true
title: "wait_child · moxie function"
---

# `wait_child`

<p class="specref"><a href="../reference.html#fn-wait_child">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn wait_child(c Child) Result[Int, Error]
```

## Description {#description}

Waits for a program started with `spawn` to finish. Other fibers run meanwhile.

**Parameters**

- `c`: a `Child`.

**Returns** `Ok(exit code)`, or `Err`.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> wait_child(c)
Ok(0)
```

