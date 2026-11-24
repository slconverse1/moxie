---
layout: default
toc: true
terms: true
dialect: gc
title: "raw_terminal · moxie/gc function"
---

# `raw_terminal`

<p class="specref"><a href="../reference.html#fn-raw_terminal">The alphabetical list</a> · <a href="../spec.html#s19b">Spec §19b</a></p>

## Signature {#signature}

```
fn raw_terminal() Result[Terminal, Error]
```

## Description {#description}

Puts the terminal into raw mode, so single key presses arrive at once instead of whole lines, as a game or editor needs. The terminal is put back when the `Terminal` is closed or the program ends.

**Parameters** none.

**Returns** `Ok(Terminal)`, or `Err` when there is no terminal (for instance when input is piped).

## Effects {#effects}

**Effect:** uses the system

**Needs permission:** stdin

## Examples {#examples}

```
> raw_terminal()
Ok(Terminal())
```

