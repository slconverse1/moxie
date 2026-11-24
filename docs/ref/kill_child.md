---
layout: default
toc: true
terms: true
title: "kill_child · moxie function"
---

# `kill_child`

<p class="specref"><a href="../reference.html#fn-kill_child">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn kill_child(c Child) Unit
```

## Description {#description}

Stops a program started with `spawn`.

**Parameters**

- `c`: a `Child`.

**Returns** nothing.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> kill_child(c)
the program is stopped
```

