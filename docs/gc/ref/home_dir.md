---
layout: default
toc: true
terms: true
dialect: gc
title: "home_dir · moxie/gc function"
---

# `home_dir`

<p class="specref"><a href="../reference.html#fn-home_dir">The alphabetical list</a> · <a href="../spec.html#s19c">Spec §19c</a></p>

## Signature {#signature}

```
fn home_dir() Result[String, Error]
```

## Description {#description}

The current user's home folder.

**Parameters** none.

**Returns** `Ok(path)`, or `Err` if the system doesn't say.

## Effects {#effects}

**Effect:** uses the system

## Examples {#examples}

```
> home_dir()
Ok("/home/ada")
```

