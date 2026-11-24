---
layout: default
toc: true
terms: true
dialect: gc
title: "cwd · moxie/gc function"
---

# `cwd`

<p class="specref"><a href="../reference.html#fn-cwd">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn cwd() String
```

## Description {#description}

The folder the program was started in.

**Parameters** none.

**Returns** a `String`.

## Effects {#effects}

**Effect:** uses the system

## Examples {#examples}

```
> cwd()
"/home/ada/project"
```

