---
layout: default
toc: true
terms: true
dialect: gc
title: "read_key · moxie/gc function"
---

# `read_key`

<p class="specref"><a href="../reference.html#fn-read_key">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn read_key(t Terminal) Result[Key, Error]
```

## Description {#description}

Waits for one key press on a raw terminal.

**Parameters**

- `t`: a `Terminal` from `raw_terminal`.

**Returns** `Ok(Key)`, or `Err`.

## Effects {#effects}

**Effect:** parks

## Examples {#examples}

```
> read_key(t)
Ok(Key.Char('q'))
```

