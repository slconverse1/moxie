---
layout: default
toc: true
terms: true
title: "hostname · moxie function"
---

# `hostname`

<p class="specref"><a href="../reference.html#fn-hostname">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn hostname() String
```

## Description {#description}

The name of this computer.

**Parameters** none.

**Returns** a `String`.

## Effects {#effects}

**Effect:** uses the system

## Examples {#examples}

```
> hostname()
"ada-laptop"
```

