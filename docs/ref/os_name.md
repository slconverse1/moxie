---
layout: default
toc: true
terms: true
title: "os_name · moxie function"
---

# `os_name`

<p class="specref"><a href="../reference.html#fn-os_name">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn os_name() String
```

## Description {#description}

The name of the operating system: `"linux"`, `"macos"` or `"windows"`.

**Parameters** none.

**Returns** a `String`.

## Effects {#effects}

**Effect:** uses the system

## Examples {#examples}

```
> os_name() == "linux" or os_name() == "macos" or os_name() == "windows"
true
```

