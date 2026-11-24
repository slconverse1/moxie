---
layout: default
toc: true
terms: true
title: "temp_dir · moxie function"
---

# `temp_dir`

<p class="specref"><a href="../reference.html#fn-temp_dir">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn temp_dir() String
```

## Description {#description}

The folder the system offers for temporary files.

**Parameters** none.

**Returns** a `String`.

## Effects {#effects}

**Effect:** uses the system

## Examples {#examples}

```
> temp_dir()
"/tmp"
```

